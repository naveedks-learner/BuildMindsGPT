import json
import os
import uuid
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict

import streamlit as st
from openai import OpenAI, OpenAIError
from streamlit.errors import StreamlitSecretNotFoundError


MODEL = "openai/gpt-4o-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
CHATS_DIR = Path(
    os.environ.get("CHAT_STORAGE_DIR", Path(__file__).parent / "chats")
)
DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, accurate assistant. Be clear about uncertainty."
)


class ChatMessage(TypedDict):
    role: str
    content: str


class Chat(TypedDict):
    title: str
    messages: list[ChatMessage]
    updated_at: str


st.set_page_config(page_title="BuildmindsGPT", page_icon="💬")


def get_api_key() -> str:
    """Read an explicit local environment override or Streamlit secret."""
    environment_key = os.environ.get("OPENROUTER_API_KEY")
    if environment_key is not None:
        return environment_key.strip()
    try:
        secret_key = str(st.secrets.get("OPENROUTER_API_KEY", "")).strip()
    except StreamlitSecretNotFoundError:
        secret_key = ""
    return secret_key


def stream_response(
    client: OpenAI,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
) -> Iterator[str]:
    """Yield response text from the OpenRouter Chat Completions stream."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )
    for chunk in response:
        if not chunk.choices:
            continue
        text = chunk.choices[0].delta.content
        if isinstance(text, str) and text:
            yield text


def chat_path(chat_id: str) -> Path:
    """Return the JSON file for a generated chat ID."""
    return CHATS_DIR / f"{chat_id}.json"


def save_chat(chat_id: str, chat: Chat) -> None:
    """Persist a conversation using an atomic file replacement."""
    CHATS_DIR.mkdir(parents=True, exist_ok=True)
    chat["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    data = {
        "id": chat_id,
        "title": chat["title"],
        "updated_at": chat["updated_at"],
        "messages": chat["messages"],
    }
    path = chat_path(chat_id)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def load_saved_chats() -> tuple[dict[str, Chat], list[str]]:
    """Load valid JSON conversations and report files that could not be read."""
    chats: dict[str, Chat] = {}
    invalid_files: list[str] = []
    if not CHATS_DIR.exists():
        return chats, invalid_files

    for path in CHATS_DIR.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Chat data must be an object.")

            chat_id = data.get("id", path.stem)
            title = data.get("title", "New chat")
            updated_at = data.get("updated_at", "")
            raw_messages = data.get("messages", [])
            if (
                not isinstance(chat_id, str)
                or chat_id != path.stem
                or not isinstance(title, str)
                or not isinstance(updated_at, str)
                or not isinstance(raw_messages, list)
            ):
                raise ValueError("Chat data has an invalid shape.")

            messages: list[ChatMessage] = []
            for message in raw_messages:
                if (
                    not isinstance(message, dict)
                    or not isinstance(message.get("role"), str)
                    or message["role"] not in {"user", "assistant"}
                    or not isinstance(message.get("content"), str)
                ):
                    raise ValueError("A chat message has an invalid shape.")
                messages.append(
                    {
                        "role": message["role"],
                        "content": message["content"],
                    }
                )

            chats[chat_id] = {
                "title": title,
                "messages": messages,
                "updated_at": updated_at,
            }
        except (OSError, json.JSONDecodeError, ValueError):
            invalid_files.append(path.name)

    return dict(
        sorted(
            chats.items(),
            key=lambda item: item[1]["updated_at"],
            reverse=True,
        )
    ), invalid_files


def start_new_chat() -> None:
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "New chat",
        "messages": [],
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    st.session_state.active_chat_id = chat_id


def delete_saved_chat(chat_id: str) -> None:
    """Remove a conversation file if it has been saved."""
    path = chat_path(chat_id)
    path.unlink(missing_ok=True)


def main() -> None:
    if "chats" not in st.session_state:
        chats, invalid_files = load_saved_chats()
        st.session_state.chats = chats
        st.session_state.invalid_chat_files = invalid_files
    st.session_state.setdefault("invalid_chat_files", [])
    st.session_state.setdefault("temperature", 0.7)
    st.session_state.setdefault("max_tokens", 1024)
    st.session_state.setdefault("context_messages", 20)
    st.session_state.setdefault("streaming", True)
    st.session_state.setdefault("system_prompt", DEFAULT_SYSTEM_PROMPT)
    st.session_state.setdefault(
        "system_prompt_draft", st.session_state.system_prompt
    )

    if not st.session_state.chats:
        start_new_chat()
    if st.session_state.get("active_chat_id") not in st.session_state.chats:
        st.session_state.active_chat_id = next(iter(st.session_state.chats))

    st.sidebar.title("BuildmindsGPT")
    st.sidebar.caption("GPT-4o mini via OpenRouter")

    if st.sidebar.button(":material/add: New chat", width="stretch"):
        start_new_chat()
        st.rerun()

    st.sidebar.subheader("History")
    for chat_id, chat in sorted(
        st.session_state.chats.items(),
        key=lambda item: item[1]["updated_at"],
        reverse=True,
    ):
        if st.sidebar.button(
            chat["title"],
            key=f"chat-{chat_id}",
            type=(
                "primary"
                if chat_id == st.session_state.active_chat_id
                else "secondary"
            ),
            width="stretch",
        ):
            st.session_state.active_chat_id = chat_id
            st.rerun()

    active_chat_id = st.session_state.active_chat_id
    active_chat = st.session_state.chats[active_chat_id]

    if st.sidebar.button("Delete current chat", width="stretch"):
        try:
            delete_saved_chat(active_chat_id)
        except OSError as error:
            st.error(f"Could not delete the saved chat: {error}")
        else:
            del st.session_state.chats[active_chat_id]
            if not st.session_state.chats:
                start_new_chat()
            else:
                st.session_state.active_chat_id = next(
                    iter(st.session_state.chats)
                )
            st.rerun()

    with st.sidebar.expander("Settings"):
        st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            step=0.1,
            key="temperature",
            help="Lower values are more focused; higher values are more varied.",
        )
        st.slider(
            "Maximum output tokens",
            min_value=128,
            max_value=4096,
            step=128,
            key="max_tokens",
        )
        st.slider(
            "Recent messages to include",
            min_value=2,
            max_value=40,
            step=2,
            key="context_messages",
            help="Limits how much chat history is sent with each request.",
        )
        st.toggle("Stream responses", key="streaming")
        prompt_column, save_column = st.columns([4, 1], vertical_alignment="top")
        with prompt_column:
            st.text_area(
                "System prompt",
                key="system_prompt_draft",
                height=120,
                help="Edit the prompt, then click Save to apply it.",
            )
        with save_column:
            if st.button("Save", key="save_system_prompt", use_container_width=True):
                st.session_state.system_prompt = (
                    st.session_state.system_prompt_draft
                )
                st.caption("Saved for this session.")
        st.caption("Use Settings > Theme in the app menu to switch appearance.")

    st.title("BuildmindsGPT")
    st.caption(
        "Chat history is saved in local JSON files. Everyone using this "
        "deployment shares the same history."
    )
    if st.session_state.invalid_chat_files:
        st.warning(
            "Some saved chats could not be loaded: "
            + ", ".join(st.session_state.invalid_chat_files)
        )

    for message in active_chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input(
        "Message BuildmindsGPT",
        submit_mode="disable",
    )
    if not prompt or not prompt.strip():
        return

    active_chat["messages"].append({"role": "user", "content": prompt})
    if len(active_chat["messages"]) == 1:
        active_chat["title"] = prompt.strip().replace("\n", " ")[:36]
    try:
        save_chat(active_chat_id, active_chat)
    except OSError as error:
        st.error(f"Could not save chat history: {error}")
        return

    with st.chat_message("user"):
        st.markdown(prompt)

    api_key = get_api_key()
    if not api_key:
        st.error(
            "OpenRouter API key is missing. Add OPENROUTER_API_KEY to "
            "Streamlit secrets, or set it in your local environment."
        )
        return

    recent_messages = active_chat["messages"][-st.session_state.context_messages :]
    request_messages = [
        {
            "role": "system",
            "content": (
                st.session_state.system_prompt.strip()
                or DEFAULT_SYSTEM_PROMPT
            ),
        },
        *recent_messages,
    ]
    client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL)

    with st.chat_message("assistant"):
        try:
            if st.session_state.streaming:
                answer = st.write_stream(
                    stream_response(
                        client,
                        request_messages,
                        st.session_state.temperature,
                        st.session_state.max_tokens,
                    )
                )
            else:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=request_messages,
                    temperature=st.session_state.temperature,
                    max_tokens=st.session_state.max_tokens,
                )
                answer = (
                    response.choices[0].message.content
                    if response.choices
                    else ""
                ) or ""
                st.markdown(answer)
        except OpenAIError as error:
            error_message = str(error).replace(api_key, "[redacted]")
            st.error(f"OpenRouter request failed: {error_message}")
            return

    if not isinstance(answer, str) or not answer.strip():
        st.error("OpenRouter returned an empty response.")
        return
    active_chat["messages"].append(
        {"role": "assistant", "content": answer}
    )
    try:
        save_chat(active_chat_id, active_chat)
    except OSError as error:
        st.error(f"Could not save chat history: {error}")


if __name__ == "__main__":
    main()

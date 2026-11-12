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
APP_STYLES = """
<style>
.stApp {
    background: var(--background-color);
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] {
    max-width: 940px;
    padding-top: 1.15rem;
    padding-bottom: 6rem;
}
[data-testid="stSidebar"] {
    background: var(--secondary-background-color);
    border-right: 1px solid var(--border-color);
    text-align: left;
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.3rem; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] {
    align-items: stretch;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
[data-testid="stMainBlockContainer"] h1,
[data-testid="stMainBlockContainer"] h2,
[data-testid="stMainBlockContainer"] h3,
[data-testid="stMainBlockContainer"] p,
[data-testid="stMainBlockContainer"] label,
[data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"],
[data-testid="stMainBlockContainer"] [data-testid="stChatMessageContent"] {
    text-align: left;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
.stApp h1, .stApp h2, .stApp h3 {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    letter-spacing: -0.035em;
}
.brand-mark {
    display: flex; align-items: center; gap: .65rem;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 1.22rem;
    font-weight: 700; letter-spacing: -.04em; margin: .15rem 0 .1rem;
}
.brand-icon {
    display: inline-flex; align-items: center; justify-content: center;
    width: 1.9rem; height: 1.9rem; border-radius: .65rem;
    color: white; font-size: 1.1rem;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
}
[data-testid="stSidebar"] [data-testid="stBaseButton-primary"] {
    background: color-mix(in srgb, var(--primary-color) 10%, var(--secondary-background-color));
    border: 1px solid transparent;
    color: var(--text-color);
    box-shadow: none;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"],
[data-testid="stMainBlockContainer"] [data-testid="stBaseButton-secondary"] {
    border-color: transparent;
    border-radius: .65rem;
    background: transparent;
    color: var(--text-color);
}
[data-testid="stSidebar"] .stButton button {
    display: flex;
    width: 100%;
    min-height: 2.55rem;
    text-align: left;
    justify-content: flex-start;
}
[data-testid="stSidebar"] .stButton button > div {
    flex: 1 1 auto !important;
    width: 100% !important;
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] .stButton button > div > span {
    flex: 1 1 auto !important;
    width: 100% !important;
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] .stButton button [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] .stButton button p {
    width: 100%;
    text-align: left;
}
[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
    background: color-mix(in srgb, var(--text-color) 5%, var(--secondary-background-color));
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
    border: 1px solid var(--border-color);
    border-radius: .75rem;
    background: var(--secondary-background-color);
}
[data-testid="stChatMessage"] {
    border: 0;
    border-radius: 0;
    padding: .8rem 0;
    background: transparent;
    gap: 0;
}
[data-testid^="stChatMessageAvatar"] {
    display: none !important;
}
[data-testid="stChatMessage"] > div:last-child {
    max-width: 100%;
}
[data-testid="stChatInput"] {
    border-radius: 1.5rem;
    border: 1px solid var(--border-color);
    background: var(--secondary-background-color);
    box-shadow: 0 4px 18px color-mix(in srgb, var(--text-color) 7%, transparent);
}
[data-testid="stChatInput"] textarea { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.main-heading {
    font-size: 1.08rem;
    font-weight: 650;
    letter-spacing: -.02em;
    margin: .15rem 0 1.2rem;
}
[data-testid="stSidebar"] hr { margin: .65rem 0; }
.section-caption { color: var(--text-color); opacity: .68; font-size: .88rem; }
@media (max-width: 700px) {
    [data-testid="stMainBlockContainer"] { padding: .8rem .8rem 5rem; }
}
</style>
"""


class ChatMessage(TypedDict):
    role: str
    content: str


class Chat(TypedDict):
    title: str
    messages: list[ChatMessage]
    updated_at: str


st.set_page_config(page_title="BuildmindsGPT", page_icon="💬")


def build_request_payload(
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    streaming: bool,
) -> dict[str, object]:
    """Describe the Chat Completions request, excluding transport credentials."""
    return {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": streaming,
    }


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
    received_chunks: list[dict[str, object]],
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
        received_chunks.append(json.loads(chunk.model_dump_json()))
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
    st.session_state.setdefault("model_exchanges", {})

    if not st.session_state.chats:
        start_new_chat()
    if st.session_state.get("active_chat_id") not in st.session_state.chats:
        st.session_state.active_chat_id = next(iter(st.session_state.chats))

    st.markdown(APP_STYLES, unsafe_allow_html=True)
    st.sidebar.markdown(
        """
        <div class="brand-mark">
            <span class="brand-icon">✦</span>
            <span>BuildmindsGPT</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.caption("GPT-4o mini · powered by OpenRouter")

    if st.sidebar.button(":material/add: New chat", width="stretch"):
        start_new_chat()
        st.rerun()

    st.sidebar.subheader("Recents")
    st.sidebar.caption("Shared demo — saved chats are visible to visitors.")
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
            st.session_state.model_exchanges.pop(active_chat_id, None)
            if not st.session_state.chats:
                start_new_chat()
            else:
                st.session_state.active_chat_id = next(
                    iter(st.session_state.chats)
                )
            st.rerun()

    with st.sidebar.expander("Inference Settings", expanded=False):
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

    st.markdown(
        '<div class="main-heading">BuildmindsGPT</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.invalid_chat_files:
        st.warning(
            "Some saved chats could not be loaded: "
            + ", ".join(st.session_state.invalid_chat_files)
        )

    for message in active_chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    with st.expander("Transaction Logs", expanded=False):
        st.caption(
            "Inspect the latest Chat Completions exchange for this browser "
            "session. API credentials are never included. System prompts and "
            "messages are visible here."
        )
        exchange = st.session_state.model_exchanges.get(active_chat_id)
        request_tab, response_tab = st.tabs(
            ["Request JSON", "Response JSON"]
        )
        with request_tab:
            if exchange and exchange.get("request"):
                st.json(exchange["request"], expanded=True)
            else:
                st.info(
                    "No request has been sent for this chat in this session."
                )
        with response_tab:
            if exchange and exchange.get("response") is not None:
                st.json(exchange["response"], expanded=True)
            else:
                st.info(
                    "The model response will appear here after the next request."
                )
        st.caption(
            "Tools are not currently configured. If enabled later, their "
            "schemas and tool-call results can be inspected here."
        )

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
    request_payload = build_request_payload(
        request_messages,
        st.session_state.temperature,
        st.session_state.max_tokens,
        st.session_state.streaming,
    )
    exchange = {
        "request": request_payload,
        "response": None,
    }
    st.session_state.model_exchanges[active_chat_id] = exchange
    received_chunks: list[dict[str, object]] = []

    with st.chat_message("assistant"):
        try:
            if st.session_state.streaming:
                answer = st.write_stream(
                    stream_response(
                        client,
                        request_messages,
                        st.session_state.temperature,
                        st.session_state.max_tokens,
                        received_chunks,
                    )
                )
                exchange["response"] = {
                    "stream": True,
                    "chunks": received_chunks,
                }
            else:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=request_messages,
                    temperature=st.session_state.temperature,
                    max_tokens=st.session_state.max_tokens,
                )
                exchange["response"] = response.model_dump(mode="json")
                answer = (
                    response.choices[0].message.content
                    if response.choices
                    else ""
                ) or ""
                st.markdown(answer)
        except OpenAIError as error:
            error_message = str(error).replace(api_key, "[redacted]")
            exchange["response"] = {"error": error_message}
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

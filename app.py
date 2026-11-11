import os
import uuid
from collections.abc import Iterator

import streamlit as st
from openai import OpenAI, OpenAIError
from streamlit.errors import StreamlitSecretNotFoundError


MODEL = "openai/gpt-4o-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, accurate assistant. Be clear about uncertainty."
)

st.set_page_config(page_title="BuildmindsGPT", page_icon="💬")


def get_api_key() -> str:
    """Read the OpenRouter key from Streamlit secrets or local environment."""
    try:
        secret_key = str(st.secrets.get("OPENROUTER_API_KEY", "")).strip()
    except StreamlitSecretNotFoundError:
        secret_key = ""
    return secret_key or os.environ.get("OPENROUTER_API_KEY", "").strip()


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


def start_new_chat() -> None:
    chat_id = str(uuid.uuid4())
    st.session_state.chats[chat_id] = {
        "title": "New chat",
        "messages": [],
    }
    st.session_state.active_chat_id = chat_id


def main() -> None:
    st.session_state.setdefault("chats", {})
    st.session_state.setdefault("temperature", 0.7)
    st.session_state.setdefault("max_tokens", 1024)
    st.session_state.setdefault("context_messages", 20)
    st.session_state.setdefault("streaming", True)
    st.session_state.setdefault("system_prompt", DEFAULT_SYSTEM_PROMPT)

    if not st.session_state.chats:
        start_new_chat()
    if st.session_state.active_chat_id not in st.session_state.chats:
        st.session_state.active_chat_id = next(iter(st.session_state.chats))

    st.sidebar.title("BuildmindsGPT")
    st.sidebar.caption("GPT-4o mini via OpenRouter")

    if st.sidebar.button(":material/add: New chat", width="stretch"):
        start_new_chat()
        st.rerun()

    st.sidebar.subheader("History")
    for chat_id, chat in reversed(list(st.session_state.chats.items())):
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
        st.text_area(
            "System prompt",
            key="system_prompt",
            height=120,
            help="This instruction guides the assistant's replies.",
        )
        st.caption("Use Settings > Theme in the app menu to switch appearance.")

    st.title("BuildmindsGPT")
    st.caption(
        "A beginner chat app. History lasts for this browser session only."
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


if __name__ == "__main__":
    main()

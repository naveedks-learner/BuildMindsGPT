from collections.abc import Iterator
from typing import Any

from openai import OpenAI
import tiktoken


MODEL = "openai/gpt-4o-mini"
BASE_URL = "https://openrouter.ai/api/v1"
ENCODING = tiktoken.get_encoding("o200k_base")
MESSAGE_OVERHEAD_TOKENS = 4


def estimate_tokens(text: str) -> int:
    return len(ENCODING.encode(text))


def _estimate_message_tokens(text: str) -> int:
    return estimate_tokens(text) + MESSAGE_OVERHEAD_TOKENS


def build_messages(
    system_prompt: str,
    history: list[dict[str, Any]],
    context_window_tokens: int,
    max_output_tokens: int,
) -> list[dict[str, str]]:
    input_budget = context_window_tokens - max_output_tokens
    system_tokens = _estimate_message_tokens(system_prompt)
    if input_budget <= system_tokens:
        raise ValueError(
            "The output-token limit leaves no room for the system prompt. "
            "Increase the context window or lower the output-token limit."
        )

    messages = [{"role": "system", "content": system_prompt}]
    remaining_tokens = input_budget - system_tokens
    selected: list[dict[str, str]] = []

    for item in reversed(history):
        content = item.get("context_content") or item["content"]
        cost = _estimate_message_tokens(content)
        if cost <= remaining_tokens:
            selected.append({"role": item["role"], "content": content})
            remaining_tokens -= cost
            continue

        content_budget = remaining_tokens - MESSAGE_OVERHEAD_TOKENS
        if not selected and content_budget > 0:
            marker = "\n[Shortened to fit context.]"
            content_tokens = ENCODING.encode(content)
            marker_tokens = estimate_tokens(marker)
            add_marker = content_budget >= marker_tokens
            allowed_tokens = (
                content_budget - marker_tokens if add_marker else content_budget
            )
            truncated = ENCODING.decode(content_tokens[:allowed_tokens])
            shortened = truncated + (marker if add_marker else "")
            while add_marker and estimate_tokens(shortened) > content_budget:
                allowed_tokens -= 1
                truncated = ENCODING.decode(content_tokens[:allowed_tokens])
                shortened = truncated + marker
            selected.append(
                {
                    "role": item["role"],
                    "content": shortened,
                }
            )
        break

    messages.extend(reversed(selected))
    return messages


def complete_chat(
    api_key: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_output_tokens: int,
) -> str:
    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_output_tokens,
    )
    if not response.choices:
        return ""
    return response.choices[0].message.content or ""


def stream_chat(
    api_key: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_output_tokens: int,
) -> Iterator[str]:
    client = OpenAI(api_key=api_key, base_url=BASE_URL)
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_output_tokens,
        stream=True,
    )
    for chunk in response:
        if not chunk.choices:
            continue
        text = chunk.choices[0].delta.content
        if isinstance(text, str) and text:
            yield text

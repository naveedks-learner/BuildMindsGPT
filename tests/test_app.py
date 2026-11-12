import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class ChatAppTests(unittest.TestCase):
    def test_app_renders_a_new_session_chat(self) -> None:
        with tempfile.TemporaryDirectory() as chat_dir:
            with patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "",
                    "CHAT_STORAGE_DIR": chat_dir,
                },
            ):
                app = AppTest.from_file(
                    Path(__file__).resolve().parents[1] / "app.py"
                ).run(timeout=30)

        self.assertFalse(app.exception)
        self.assertTrue(
            any("BuildmindsGPT" in item.value for item in app.markdown)
        )
        self.assertEqual(app.sidebar.subheader[0].value, "Recents")
        self.assertEqual(len(app.session_state["chats"]), 1)
        self.assertEqual(
            app.session_state["chats"][
                app.session_state["active_chat_id"]
            ]["messages"],
            [],
        )

    def test_new_chat_keeps_the_existing_chat_separate(self) -> None:
        with tempfile.TemporaryDirectory() as chat_dir:
            with patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "",
                    "CHAT_STORAGE_DIR": chat_dir,
                },
            ):
                app = AppTest.from_file(
                    Path(__file__).resolve().parents[1] / "app.py"
                ).run(timeout=30)
                app.sidebar.button[0].click().run(timeout=30)

        self.assertFalse(app.exception)
        self.assertEqual(len(app.session_state["chats"]), 2)
        self.assertNotEqual(
            app.session_state["active_chat_id"],
            next(iter(app.session_state["chats"])),
        )

    def test_missing_api_key_is_shown_after_a_message(self) -> None:
        with tempfile.TemporaryDirectory() as chat_dir:
            with patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "",
                    "CHAT_STORAGE_DIR": chat_dir,
                },
            ):
                app = AppTest.from_file(
                    Path(__file__).resolve().parents[1] / "app.py"
                ).run(timeout=30)
                app.chat_input[0].set_value("Hello").run(timeout=30)
                saved_file_count = len(list(Path(chat_dir).glob("*.json")))

        self.assertFalse(app.exception)
        self.assertTrue(
            any("OpenRouter API key is missing" in item.value for item in app.error)
        )
        messages = app.session_state["chats"][
            app.session_state["active_chat_id"]
        ]["messages"]
        self.assertEqual(messages, [{"role": "user", "content": "Hello"}])
        self.assertEqual(saved_file_count, 1)

    def test_saved_chat_is_restored_in_a_new_session(self) -> None:
        with tempfile.TemporaryDirectory() as chat_dir:
            with patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "",
                    "CHAT_STORAGE_DIR": chat_dir,
                },
            ):
                app = AppTest.from_file(
                    Path(__file__).resolve().parents[1] / "app.py"
                ).run(timeout=30)
                app.chat_input[0].set_value("Hello").run(timeout=30)
                chat_id = app.session_state["active_chat_id"]
                saved = json.loads(
                    next(Path(chat_dir).glob("*.json")).read_text(
                        encoding="utf-8"
                    )
                )
                app = AppTest.from_file(
                    Path(__file__).resolve().parents[1] / "app.py"
                ).run(timeout=30)

        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["active_chat_id"], chat_id)
        self.assertEqual(
            app.session_state["chats"][chat_id]["messages"],
            [{"role": "user", "content": "Hello"}],
        )
        self.assertEqual(saved["id"], chat_id)

    def test_deleting_current_chat_removes_its_saved_file(self) -> None:
        with tempfile.TemporaryDirectory() as chat_dir:
            with patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "",
                    "CHAT_STORAGE_DIR": chat_dir,
                },
            ):
                app = AppTest.from_file(
                    Path(__file__).resolve().parents[1] / "app.py"
                ).run(timeout=30)
                app.chat_input[0].set_value("Hello").run(timeout=30)
                delete_button = next(
                    button
                    for button in app.sidebar.button
                    if button.label == "Delete current chat"
                )
                delete_button.click().run(timeout=30)
                remaining_file_count = len(
                    list(Path(chat_dir).glob("*.json"))
                )

        self.assertFalse(app.exception)
        self.assertEqual(remaining_file_count, 0)

    def test_system_prompt_is_applied_when_save_is_clicked(self) -> None:
        with tempfile.TemporaryDirectory() as chat_dir:
            with patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "",
                    "CHAT_STORAGE_DIR": chat_dir,
                },
            ):
                app = AppTest.from_file(
                    Path(__file__).resolve().parents[1] / "app.py"
                ).run(timeout=30)
                updated_prompt = "Answer in concise bullet points."
                app.sidebar.text_area[0].set_value(updated_prompt).run(
                    timeout=30
                )
                prompt_before_save = app.session_state["system_prompt"]
                save_button = next(
                    button
                    for button in app.sidebar.button
                    if button.label == "Save"
                )
                save_button.click().run(timeout=30)

        self.assertFalse(app.exception)
        self.assertNotEqual(prompt_before_save, updated_prompt)
        self.assertEqual(app.session_state["system_prompt"], updated_prompt)

    def test_settings_inspector_captures_request_and_response_json(self) -> None:
        with tempfile.TemporaryDirectory() as chat_dir:
            with patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "test-key",
                    "CHAT_STORAGE_DIR": chat_dir,
                },
            ):
                response_json = {
                    "id": "test-completion",
                    "choices": [
                        {"message": {"role": "assistant", "content": "Hello"}}
                    ],
                }
                response = SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content="Hello")
                        )
                    ],
                    model_dump=lambda mode: response_json,
                )
                client = SimpleNamespace(
                    chat=SimpleNamespace(
                        completions=SimpleNamespace(
                            create=lambda **kwargs: response
                        )
                    )
                )
                with patch("openai.OpenAI", return_value=client) as openai_client:
                    app = AppTest.from_file(
                        Path(__file__).resolve().parents[1] / "app.py"
                    ).run(timeout=30)
                    app.session_state["streaming"] = False
                    app.chat_input[0].set_value("Hello").run(timeout=30)

        self.assertFalse(app.exception)
        openai_client.assert_called_once()
        exchange = app.session_state["model_exchanges"][
            app.session_state["active_chat_id"]
        ]
        self.assertEqual(exchange["request"]["model"], "openai/gpt-4o-mini")
        self.assertEqual(exchange["request"]["messages"][0]["role"], "system")
        self.assertFalse(exchange["request"]["stream"])
        self.assertEqual(exchange["response"], response_json)
        self.assertNotIn("test-key", json.dumps(exchange))

    def test_settings_inspector_captures_raw_stream_chunks(self) -> None:
        with tempfile.TemporaryDirectory() as chat_dir:
            with patch.dict(
                os.environ,
                {
                    "OPENROUTER_API_KEY": "test-key",
                    "CHAT_STORAGE_DIR": chat_dir,
                },
            ):
                stream_chunk_json = (
                    '{"id":"test-chunk","choices":[{"delta":'
                    '{"content":"Hello"}}]}'
                )
                chunk = SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            delta=SimpleNamespace(content="Hello")
                        )
                    ],
                    model_dump_json=lambda: stream_chunk_json,
                )
                client = SimpleNamespace(
                    chat=SimpleNamespace(
                        completions=SimpleNamespace(
                            create=lambda **kwargs: iter([chunk])
                        )
                    )
                )
                with patch("openai.OpenAI", return_value=client):
                    app = AppTest.from_file(
                        Path(__file__).resolve().parents[1] / "app.py"
                    ).run(timeout=30)
                    app.chat_input[0].set_value("Hello").run(timeout=30)

        self.assertFalse(app.exception)
        exchange = app.session_state["model_exchanges"][
            app.session_state["active_chat_id"]
        ]
        self.assertTrue(exchange["request"]["stream"])
        self.assertEqual(
            exchange["response"]["chunks"],
            [json.loads(stream_chunk_json)],
        )


if __name__ == "__main__":
    unittest.main()

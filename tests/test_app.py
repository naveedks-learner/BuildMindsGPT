import os
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


class ChatAppTests(unittest.TestCase):
    def test_app_renders_a_new_session_chat(self) -> None:
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
            app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run(
                timeout=30
            )

        self.assertFalse(app.exception)
        self.assertTrue(app.title)
        self.assertEqual(len(app.session_state["chats"]), 1)
        self.assertEqual(
            app.session_state["chats"][
                app.session_state["active_chat_id"]
            ]["messages"],
            [],
        )

    def test_new_chat_keeps_the_existing_chat_separate(self) -> None:
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
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
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
            app = AppTest.from_file(Path(__file__).resolve().parents[1] / "app.py").run(
                timeout=30
            )
            app.chat_input[0].set_value("Hello").run(timeout=30)

        self.assertFalse(app.exception)
        self.assertTrue(
            any("OpenRouter API key is missing" in item.value for item in app.error)
        )
        messages = app.session_state["chats"][
            app.session_state["active_chat_id"]
        ]["messages"]
        self.assertEqual(messages, [{"role": "user", "content": "Hello"}])


if __name__ == "__main__":
    unittest.main()

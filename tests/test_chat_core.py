import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import chat_storage
from openrouter_client import (
    MESSAGE_OVERHEAD_TOKENS,
    build_messages,
    estimate_tokens,
)


class ContextWindowTests(unittest.TestCase):
    def test_keeps_newest_turn_when_older_turns_exceed_budget(self) -> None:
        messages = build_messages(
            "x",
            [
                {"role": "user", "content": "old " * 20},
                {"role": "assistant", "content": "older answer " * 20},
                {"role": "user", "content": "latest"},
            ],
            context_window_tokens=32,
            max_output_tokens=8,
        )

        self.assertEqual(messages[0], {"role": "system", "content": "x"})
        self.assertEqual(
            messages[1],
            {"role": "user", "content": "latest"},
        )
        self.assertEqual(len(messages), 2)
        used_tokens = sum(
            estimate_tokens(message["content"]) + MESSAGE_OVERHEAD_TOKENS
            for message in messages
        )
        self.assertLessEqual(used_tokens, 32 - 8)

    def test_truncates_a_single_turn_to_the_remaining_budget(self) -> None:
        messages = build_messages(
            "x",
            [{"role": "user", "content": "a" * 100}],
            context_window_tokens=32,
            max_output_tokens=8,
        )

        self.assertLessEqual(estimate_tokens(messages[1]["content"]), 15)
        used_tokens = sum(
            estimate_tokens(message["content"]) + MESSAGE_OVERHEAD_TOKENS
            for message in messages
        )
        self.assertLessEqual(used_tokens, 32 - 8)

    def test_rejects_output_limit_that_leaves_no_input_budget(self) -> None:
        with self.assertRaises(ValueError):
            build_messages(
                "system prompt",
                [{"role": "user", "content": "question"}],
                context_window_tokens=10,
                max_output_tokens=10,
            )


class ChatStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_database_path = chat_storage.DATABASE_PATH
        chat_storage.DATABASE_PATH = Path(self.temp_dir.name) / "history.sqlite3"
        chat_storage.initialize_database()

    def tearDown(self) -> None:
        chat_storage.DATABASE_PATH = self.original_database_path
        self.temp_dir.cleanup()

    def test_messages_persist_and_delete_with_conversation(self) -> None:
        conversation_id = chat_storage.create_conversation("A test chat")
        chat_storage.add_message(
            conversation_id,
            "user",
            "Summarize this.",
            context_content="Summarize this.\nDocument text",
            attachments=["notes.txt"],
        )
        chat_storage.add_message(
            conversation_id,
            "assistant",
            "Here is the summary.",
        )

        history = chat_storage.get_messages(conversation_id)
        self.assertEqual([item["role"] for item in history], ["user", "assistant"])
        self.assertEqual(history[0]["attachments"], ["notes.txt"])
        self.assertEqual(
            history[0]["context_content"],
            "Summarize this.\nDocument text",
        )
        self.assertEqual(chat_storage.list_conversations()[0]["id"], conversation_id)

        chat_storage.delete_conversation(conversation_id)
        self.assertEqual(chat_storage.list_conversations(), [])
        self.assertEqual(chat_storage.get_messages(conversation_id), [])

    def test_postgres_uses_transaction_pooler_compatible_driver_options(self) -> None:
        class FakeConnection:
            def __init__(self) -> None:
                self.queries: list[tuple[str, tuple[object, ...]]] = []
                self.committed = False
                self.closed = False

            def execute(
                self,
                query: str,
                parameters: tuple[object, ...] = (),
            ) -> "FakeConnection":
                self.queries.append((query, parameters))
                return self

            def commit(self) -> None:
                self.committed = True

            def rollback(self) -> None:
                raise AssertionError("Unexpected rollback")

            def close(self) -> None:
                self.closed = True

        connection = FakeConnection()
        database_url = "postgresql://example"
        with patch.object(
            chat_storage.psycopg,
            "connect",
            return_value=connection,
        ) as connect:
            chat_storage.initialize_database(database_url)
            conversation_id = chat_storage.create_conversation(
                "Postgres test",
                database_url,
            )

        self.assertEqual(connect.call_args.kwargs["prepare_threshold"], None)
        self.assertEqual(connect.call_args.kwargs["row_factory"], chat_storage.dict_row)
        self.assertTrue(connection.committed)
        self.assertTrue(connection.closed)
        self.assertEqual(len(connection.queries), 4)
        insert_query, insert_parameters = connection.queries[-1]
        self.assertIn("VALUES (%s, %s)", insert_query)
        self.assertEqual(insert_parameters, (conversation_id, "Postgres test"))


if __name__ == "__main__":
    unittest.main()

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import psycopg
from psycopg.rows import dict_row


DATABASE_PATH = Path(os.environ.get("CHAT_DB_PATH", ".data/chat_history.sqlite3"))


@contextmanager
def _connect(database_url: str | None = None) -> Generator[Any, None, None]:
    if database_url:
        connection = psycopg.connect(
            database_url,
            row_factory=dict_row,
            prepare_threshold=None,
        )
    else:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(DATABASE_PATH, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def _execute(
    connection: Any,
    query: str,
    parameters: tuple[Any, ...] = (),
    database_url: str | None = None,
) -> Any:
    if database_url:
        query = query.replace("?", "%s")
    return connection.execute(query, parameters)


def initialize_database(database_url: str | None = None) -> None:
    if database_url:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES conversations(id)
                    ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                context_content TEXT,
                attachments TEXT NOT NULL DEFAULT '[]',
                sequence BIGSERIAL UNIQUE NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS messages_conversation_sequence
                ON messages(conversation_id, sequence)
            """,
        ]
        with _connect(database_url) as connection:
            for statement in statements:
                connection.execute(statement)
        return

    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL REFERENCES conversations(id)
                    ON DELETE CASCADE,
                role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                context_content TEXT,
                attachments TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS messages_conversation_created
                ON messages(conversation_id, created_at);
            """
        )


def create_conversation(
    title: str,
    database_url: str | None = None,
) -> str:
    conversation_id = str(uuid.uuid4())
    with _connect(database_url) as connection:
        _execute(
            connection,
            "INSERT INTO conversations (id, title) VALUES (?, ?)",
            (conversation_id, title[:80] or "New chat"),
            database_url,
        )
    return conversation_id


def list_conversations(database_url: str | None = None) -> list[dict[str, Any]]:
    with _connect(database_url) as connection:
        rows = _execute(
            connection,
            """
            SELECT id, title, created_at, updated_at
            FROM conversations
            ORDER BY updated_at DESC, created_at DESC
            """,
            database_url=database_url,
        ).fetchall()
    return [dict(row) for row in rows]


def get_messages(
    conversation_id: str,
    database_url: str | None = None,
) -> list[dict[str, Any]]:
    order_by = "sequence" if database_url else "rowid"
    with _connect(database_url) as connection:
        rows = _execute(
            connection,
            f"""
            SELECT role, content, context_content, attachments, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY {order_by}
            """,
            (conversation_id,),
            database_url,
        ).fetchall()
    messages = []
    for row in rows:
        message = dict(row)
        message["attachments"] = json.loads(message["attachments"])
        messages.append(message)
    return messages


def add_message(
    conversation_id: str,
    role: str,
    content: str,
    context_content: str | None = None,
    attachments: list[str] | None = None,
    database_url: str | None = None,
) -> None:
    with _connect(database_url) as connection:
        _execute(
            connection,
            """
            INSERT INTO messages (
                id, conversation_id, role, content, context_content, attachments
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                conversation_id,
                role,
                content,
                context_content,
                json.dumps(attachments or []),
            ),
            database_url,
        )
        _execute(
            connection,
            "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (conversation_id,),
            database_url,
        )


def delete_conversation(
    conversation_id: str,
    database_url: str | None = None,
) -> None:
    with _connect(database_url) as connection:
        _execute(
            connection,
            "DELETE FROM conversations WHERE id = ?",
            (conversation_id,),
            database_url,
        )

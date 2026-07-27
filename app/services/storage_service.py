import json
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Any


class StorageService:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._initialize_database()

    def list_categories(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT name FROM categories ORDER BY position ASC"
            ).fetchall()
            return [str(row["name"]) for row in rows]

    def replace_categories(self, categories: list[str]) -> None:
        with self._lock, self._connect() as connection:
            connection.execute("DELETE FROM categories")
            connection.executemany(
                "INSERT INTO categories (name, position) VALUES (?, ?)",
                [
                    (category, index)
                    for index, category in enumerate(categories, start=1)
                ],
            )

    def get_session(self, sender_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT sender_id, state, category, filename, updated_at
                FROM conversation_sessions
                WHERE sender_id = ?
                """,
                (sender_id,),
            ).fetchone()

            return dict(row) if row is not None else None

    def save_session(
        self,
        sender_id: str,
        state: str,
        category: str | None,
        filename: str | None,
        updated_at: float,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_sessions (sender_id, state, category, filename, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(sender_id) DO UPDATE SET
                    state = excluded.state,
                    category = excluded.category,
                    filename = excluded.filename,
                    updated_at = excluded.updated_at
                """,
                (sender_id, state, category, filename, updated_at),
            )

    def delete_session(self, sender_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "DELETE FROM conversation_sessions WHERE sender_id = ?",
                (sender_id,),
            )

    def list_sessions(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT sender_id, state, category, filename, updated_at
                FROM conversation_sessions
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_expired_sessions(self, expires_before: float) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM conversation_sessions WHERE updated_at <= ?",
                (expires_before,),
            )
            return cursor.rowcount

    def save_processing_job(
        self,
        job_id: str,
        sender: str,
        origin: str,
        created_at: str,
        status: str,
        payload: dict[str, Any],
        error: str | None = None,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO processing_jobs (id, sender, origin, created_at, status, payload, error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    sender = excluded.sender,
                    origin = excluded.origin,
                    created_at = excluded.created_at,
                    status = excluded.status,
                    payload = excluded.payload,
                    error = excluded.error
                """,
                (job_id, sender, origin, created_at, status, json.dumps(payload), error),
            )

    def list_processing_jobs(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, sender, origin, created_at, status, payload, error
                FROM processing_jobs
                ORDER BY created_at ASC
                """
            ).fetchall()
            return [self._decode_job_row(row) for row in rows]

    def delete_completed_processing_jobs(self) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM processing_jobs WHERE status = ?",
                ("CONCLUIDO",),
            )
            return cursor.rowcount

    def save_media_history(
        self,
        history_id: str,
        date: str,
        sender: str,
        origin: str,
        category: str | None,
        final_name: str | None,
        file_path: str | None,
        status: str,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO media_history (
                    id, date, sender, origin, category, final_name, file_path, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (history_id, date, sender, origin, category, final_name, file_path, status),
            )

    def list_media_history(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, date, sender, origin, category, final_name, file_path, status
                FROM media_history
                ORDER BY date ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def _initialize_database(self) -> None:
        with self._lock, self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    name TEXT PRIMARY KEY,
                    position INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS conversation_sessions (
                    sender_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    category TEXT,
                    filename TEXT,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS processing_jobs (
                    id TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    error TEXT
                );

                CREATE TABLE IF NOT EXISTS media_history (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    category TEXT,
                    final_name TEXT,
                    file_path TEXT,
                    status TEXT NOT NULL
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _decode_job_row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["payload"] = json.loads(str(data["payload"]))
        return data

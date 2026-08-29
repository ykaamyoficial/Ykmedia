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
        self._enable_wal()
        self._initialize_database()

    def _enable_wal(self) -> None:
        # WAL permite leituras concorrentes com uma escrita e persiste no arquivo
        # do banco, entao basta configurar uma vez.
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")

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
                SELECT sender_id, state, category, filename, pending_media_id, updated_at,
                    allowed_option_ids, processed_interaction_ids, interactive_created_at,
                    created_at, expires_at, last_interaction_at, origin, contact_id,
                    contact_name, greeting_sent, expiry_warning_sent, batch_filenames,
                    received_types
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
        pending_media_id: str | None,
        updated_at: float,
        allowed_option_ids: list[str] | tuple[str, ...] | None = None,
        processed_interaction_ids: list[str] | tuple[str, ...] | None = None,
        interactive_created_at: float | None = None,
        created_at: float | None = None,
        expires_at: float | None = None,
        last_interaction_at: float | None = None,
        origin: str | None = None,
        contact_id: str | None = None,
        contact_name: str | None = None,
        greeting_sent: bool = False,
        expiry_warning_sent: bool = False,
        batch_filenames: list[str] | tuple[str, ...] | None = None,
        received_types: list[str] | tuple[str, ...] | None = None,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_sessions (
                    sender_id, state, category, filename, pending_media_id, updated_at,
                    allowed_option_ids, processed_interaction_ids, interactive_created_at,
                    created_at, expires_at, last_interaction_at, origin, contact_id,
                    contact_name, greeting_sent, expiry_warning_sent, batch_filenames,
                    received_types
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(sender_id) DO UPDATE SET
                    state = excluded.state,
                    category = excluded.category,
                    filename = excluded.filename,
                    pending_media_id = excluded.pending_media_id,
                    updated_at = excluded.updated_at,
                    allowed_option_ids = excluded.allowed_option_ids,
                    processed_interaction_ids = excluded.processed_interaction_ids,
                    interactive_created_at = excluded.interactive_created_at,
                    created_at = excluded.created_at,
                    expires_at = excluded.expires_at,
                    last_interaction_at = excluded.last_interaction_at,
                    origin = excluded.origin,
                    contact_id = excluded.contact_id,
                    contact_name = excluded.contact_name,
                    greeting_sent = excluded.greeting_sent,
                    expiry_warning_sent = excluded.expiry_warning_sent,
                    batch_filenames = excluded.batch_filenames,
                    received_types = excluded.received_types
                """,
                (
                    sender_id,
                    state,
                    category,
                    filename,
                    pending_media_id,
                    updated_at,
                    json.dumps(list(allowed_option_ids or ())),
                    json.dumps(list(processed_interaction_ids or ())),
                    interactive_created_at,
                    created_at,
                    expires_at,
                    last_interaction_at,
                    origin,
                    contact_id,
                    contact_name,
                    1 if greeting_sent else 0,
                    1 if expiry_warning_sent else 0,
                    json.dumps(list(batch_filenames or ())),
                    json.dumps(list(received_types or ())),
                ),
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
                SELECT sender_id, state, category, filename, pending_media_id, updated_at,
                    allowed_option_ids, processed_interaction_ids, interactive_created_at,
                    created_at, expires_at, last_interaction_at, origin, contact_id,
                    contact_name, greeting_sent, expiry_warning_sent, batch_filenames,
                    received_types
                FROM conversation_sessions
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def list_sessions_pending_expiry_warning(
        self,
        now: float,
        warn_before: float,
    ) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT sender_id, expires_at
                FROM conversation_sessions
                WHERE expiry_warning_sent = 0
                  AND state != 'IDLE'
                  AND expires_at IS NOT NULL
                  AND expires_at > ?
                  AND expires_at <= ?
                """,
                (now, warn_before),
            ).fetchall()
            return [dict(row) for row in rows]

    def mark_expiry_warning_sent(self, sender_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE conversation_sessions SET expiry_warning_sent = 1 WHERE sender_id = ?",
                (sender_id,),
            )

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
        attempts: int = 0,
        next_attempt_at: str | None = None,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO processing_jobs (
                    id, sender, origin, created_at, status, payload, error,
                    attempts, next_attempt_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    sender = excluded.sender,
                    origin = excluded.origin,
                    created_at = excluded.created_at,
                    status = excluded.status,
                    payload = excluded.payload,
                    error = excluded.error,
                    attempts = excluded.attempts,
                    next_attempt_at = excluded.next_attempt_at
                """,
                (
                    job_id,
                    sender,
                    origin,
                    created_at,
                    status,
                    json.dumps(payload),
                    error,
                    attempts,
                    next_attempt_at,
                ),
            )

    def list_processing_jobs(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, sender, origin, created_at, status, payload, error,
                       attempts, next_attempt_at
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

    def save_contact_profile(
        self,
        sender: str,
        display_name: str | None = None,
        profile_picture_url: str | None = None,
        profile_picture_path: str | None = None,
        updated_at: str | None = None,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO contact_profiles (
                    sender, display_name, profile_picture_url, profile_picture_path, updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(sender) DO UPDATE SET
                    display_name = coalesce(excluded.display_name, contact_profiles.display_name),
                    profile_picture_url = coalesce(excluded.profile_picture_url, contact_profiles.profile_picture_url),
                    profile_picture_path = coalesce(excluded.profile_picture_path, contact_profiles.profile_picture_path),
                    updated_at = coalesce(excluded.updated_at, contact_profiles.updated_at)
                """,
                (sender, display_name, profile_picture_url, profile_picture_path, updated_at),
            )

    def get_contact_profile(self, sender: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT sender, display_name, profile_picture_url, profile_picture_path, updated_at
                FROM contact_profiles
                WHERE sender = ?
                """,
                (sender,),
            ).fetchone()
            return dict(row) if row is not None else None

    def list_media_history(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, date, sender, origin, category, final_name, file_path, status
                FROM media_history
                ORDER BY date ASC, rowid ASC
                """
            ).fetchall()
            return [dict(row) for row in rows]

    def list_media_contacts(self, search_text: str = "") -> list[dict[str, Any]]:
        normalized_search = f"%{search_text.strip().lower()}%"
        params: tuple[str, ...] = ()
        where = ""
        if search_text.strip():
            where = """
                WHERE lower(sender || ' ' || coalesce(final_name, '') || ' ' || coalesce(file_path, '') || ' ' || origin) LIKE ?
            """
            params = (normalized_search,)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT grouped.sender,
                    COUNT(*) AS media_count,
                    (
                        SELECT recent.final_name
                        FROM media_history recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.date DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_media,
                    (
                        SELECT recent.date
                        FROM media_history recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.date DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_activity
                FROM media_history grouped
                {where}
                GROUP BY grouped.sender
                ORDER BY last_activity DESC
                """,
                params,
            ).fetchall()
            return [dict(row) for row in rows]

    def list_media_by_sender(self, sender: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, date, sender, origin, category, final_name, file_path, status
                FROM media_history
                WHERE sender = ?
                ORDER BY date DESC, rowid DESC
                """,
                (sender,),
            ).fetchall()
            return [dict(row) for row in rows]

    def save_pending_media(
        self,
        message_id: str,
        sender: str,
        file_name: str | None,
        mimetype: str,
        size_bytes: int,
        staging_path: str,
        created_at: float,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO pending_media (
                    message_id, sender, file_name, mimetype, size_bytes, staging_path, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    sender = excluded.sender,
                    file_name = excluded.file_name,
                    mimetype = excluded.mimetype,
                    size_bytes = excluded.size_bytes,
                    staging_path = excluded.staging_path,
                    created_at = excluded.created_at
                """,
                (message_id, sender, file_name, mimetype, size_bytes, staging_path, created_at),
            )

    def get_pending_media(self, message_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM pending_media WHERE message_id = ?",
                (message_id,),
            ).fetchone()
            return dict(row) if row is not None else None

    def list_pending_media_before(self, cutoff: float) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM pending_media WHERE created_at < ?",
                (cutoff,),
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_pending_media(self, message_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "DELETE FROM pending_media WHERE message_id = ?",
                (message_id,),
            )

    def delete_pending_media_before(self, cutoff: float) -> int:
        with self._lock, self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM pending_media WHERE created_at < ?",
                (cutoff,),
            )
            return cursor.rowcount

    def save_media_record(
        self,
        media_id: str,
        message_id: str,
        file_name: str,
        relative_path: str,
        mimetype: str | None,
        size_bytes: int,
        sha256: str,
        absolute_path: str | None,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO media_records (
                    media_id, message_id, file_name, relative_path, mimetype,
                    size_bytes, sha256, absolute_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(media_id) DO UPDATE SET
                    message_id = excluded.message_id,
                    file_name = excluded.file_name,
                    relative_path = excluded.relative_path,
                    mimetype = excluded.mimetype,
                    size_bytes = excluded.size_bytes,
                    sha256 = excluded.sha256,
                    absolute_path = excluded.absolute_path
                """,
                (
                    media_id,
                    message_id,
                    file_name,
                    relative_path,
                    mimetype,
                    size_bytes,
                    sha256,
                    absolute_path,
                ),
            )

    def get_media_record(self, media_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM media_records WHERE media_id = ?",
                (media_id,),
            ).fetchone()
            return dict(row) if row is not None else None

    def list_media_records(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM media_records ORDER BY rowid ASC"
            ).fetchall()
            return [dict(row) for row in rows]

    def delete_media_record(self, media_id: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "DELETE FROM media_records WHERE media_id = ?",
                (media_id,),
            )

    def save_processed_message(
        self,
        message_id: str,
        sender: str,
        status: str,
        processed_at: str,
        error: str | None = None,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO processed_messages (message_id, sender, status, processed_at, error)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(message_id) DO UPDATE SET
                    sender = excluded.sender,
                    status = excluded.status,
                    processed_at = excluded.processed_at,
                    error = excluded.error
                """,
                (message_id, sender, status, processed_at, error),
            )

    def get_processed_message(self, message_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT message_id, sender, status, processed_at, error
                FROM processed_messages
                WHERE message_id = ?
                """,
                (message_id,),
            ).fetchone()

            return dict(row) if row is not None else None

    def save_conversation_message(
        self,
        record_id: str,
        message_id: str,
        sender: str,
        direction: str,
        content: str,
        message_type: str,
        state: str | None,
        media_id: str | None,
        created_at: str,
        status: str,
        error: str | None = None,
    ) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO conversation_messages (
                    id, message_id, sender, direction, content, message_type,
                    state, media_id, created_at, status, error
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    message_id = excluded.message_id,
                    sender = excluded.sender,
                    direction = excluded.direction,
                    content = excluded.content,
                    message_type = excluded.message_type,
                    state = excluded.state,
                    media_id = excluded.media_id,
                    created_at = excluded.created_at,
                    status = excluded.status,
                    error = excluded.error
                """,
                (
                    record_id,
                    message_id,
                    sender,
                    direction,
                    content,
                    message_type,
                    state,
                    media_id,
                    created_at,
                    status,
                    error,
                ),
            )

    def list_conversation_messages(self, sender: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, message_id, sender, direction, content, message_type,
                    state, media_id, created_at, status, error
                FROM conversation_messages
                WHERE sender = ?
                ORDER BY created_at ASC, rowid ASC
                """,
                (sender,),
            ).fetchall()

            return [dict(row) for row in rows]

    def list_conversation_contacts(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT grouped.sender,
                    (
                        SELECT coalesce(recent.final_name, recent.file_path)
                        FROM media_history recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.date DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_media_content,
                    (
                        SELECT recent.date
                        FROM media_history recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.date DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_media_activity,
                    (
                        SELECT COUNT(*)
                        FROM media_history recent
                        WHERE recent.sender = grouped.sender
                    ) AS media_count,
                    (
                        SELECT recent.content
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_content,
                    (
                        SELECT recent.created_at
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_activity,
                    (
                        SELECT recent.state
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_state,
                    (
                        SELECT recent.status
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_status,
                    COUNT(*) AS message_count
                FROM conversation_messages grouped
                GROUP BY grouped.sender
                ORDER BY last_activity DESC
                """
            ).fetchall()

            return [dict(row) for row in rows]

    def count_conversation_contacts(self, search_text: str = "") -> int:
        normalized_search = f"%{search_text.strip().lower()}%"
        where = ""
        params: tuple[str, ...] = ()
        if search_text.strip():
            where = """
                WHERE lower(grouped.sender || ' ' || coalesce(profile.display_name, '')) LIKE ?
            """
            params = (normalized_search,)

        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM (
                    SELECT grouped.sender
                    FROM conversation_messages grouped
                    LEFT JOIN contact_profiles profile ON profile.sender = grouped.sender
                    {where}
                    GROUP BY grouped.sender
                ) contacts
                """,
                params,
            ).fetchone()
            return int(row["total"]) if row is not None else 0

    def list_conversation_contacts_paginated(
        self,
        search_text: str = "",
        limit: int = 30,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        normalized_search = f"%{search_text.strip().lower()}%"
        where = ""
        params: tuple[Any, ...] = ()
        if search_text.strip():
            where = """
                WHERE lower(grouped.sender || ' ' || coalesce(profile.display_name, '')) LIKE ?
            """
            params = (normalized_search,)

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT grouped.sender,
                    profile.display_name,
                    profile.profile_picture_url,
                    profile.profile_picture_path,
                    sessions.state AS session_state,
                    sessions.category,
                    (
                        SELECT coalesce(recent.final_name, recent.file_path)
                        FROM media_history recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.date DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_media_content,
                    (
                        SELECT recent.date
                        FROM media_history recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.date DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_media_activity,
                    (
                        SELECT COUNT(*)
                        FROM media_history recent
                        WHERE recent.sender = grouped.sender
                    ) AS media_count,
                    (
                        SELECT recent.content
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_content,
                    (
                        SELECT recent.created_at
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_activity,
                    (
                        SELECT recent.direction
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_direction,
                    (
                        SELECT recent.state
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_state,
                    (
                        SELECT recent.status
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_status,
                    COUNT(*) AS message_count
                FROM conversation_messages grouped
                LEFT JOIN contact_profiles profile ON profile.sender = grouped.sender
                LEFT JOIN conversation_sessions sessions ON sessions.sender_id = grouped.sender
                {where}
                GROUP BY grouped.sender
                ORDER BY CASE WHEN coalesce(last_media_activity, last_activity) IS NULL THEN 1 ELSE 0 END,
                    coalesce(last_media_activity, last_activity) DESC,
                    grouped.sender ASC
                LIMIT ? OFFSET ?
                """,
                (*params, limit, offset),
            ).fetchall()

            return [dict(row) for row in rows]

    def get_conversation_contact(self, sender: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT grouped.sender,
                    profile.display_name,
                    profile.profile_picture_url,
                    profile.profile_picture_path,
                    sessions.state AS session_state,
                    sessions.category,
                    sessions.updated_at AS session_updated_at,
                    (
                        SELECT recent.content
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_content,
                    (
                        SELECT recent.created_at
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_activity,
                    (
                        SELECT recent.direction
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_direction,
                    (
                        SELECT recent.status
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at DESC, recent.rowid DESC
                        LIMIT 1
                    ) AS last_status,
                    (
                        SELECT recent.created_at
                        FROM conversation_messages recent
                        WHERE recent.sender = grouped.sender
                        ORDER BY recent.created_at ASC, recent.rowid ASC
                        LIMIT 1
                    ) AS first_activity,
                    (
                        SELECT COUNT(*)
                        FROM media_history recent
                        WHERE recent.sender = grouped.sender
                    ) AS media_count,
                    COUNT(*) AS message_count
                FROM conversation_messages grouped
                LEFT JOIN contact_profiles profile ON profile.sender = grouped.sender
                LEFT JOIN conversation_sessions sessions ON sessions.sender_id = grouped.sender
                WHERE grouped.sender = ?
                GROUP BY grouped.sender
                """,
                (sender,),
            ).fetchone()

            return dict(row) if row is not None else None

    def count_conversation_messages(self, sender: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM conversation_messages
                WHERE sender = ?
                """,
                (sender,),
            ).fetchone()
            return int(row["total"]) if row is not None else 0

    def list_conversation_messages_paginated(
        self,
        sender: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, message_id, sender, direction, content, message_type,
                    state, media_id, created_at, status, error
                FROM conversation_messages
                WHERE sender = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT ? OFFSET ?
                """,
                (sender, limit, offset),
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
                    contact_name TEXT,
                    pending_media_id TEXT,
                    allowed_option_ids TEXT NOT NULL DEFAULT '[]',
                    processed_interaction_ids TEXT NOT NULL DEFAULT '[]',
                    interactive_created_at REAL,
                    created_at REAL,
                    expires_at REAL,
                    last_interaction_at REAL,
                    origin TEXT,
                    contact_id TEXT,
                    greeting_sent INTEGER NOT NULL DEFAULT 0,
                    expiry_warning_sent INTEGER NOT NULL DEFAULT 0,
                    batch_filenames TEXT NOT NULL DEFAULT '[]',
                    received_types TEXT NOT NULL DEFAULT '[]',
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS processing_jobs (
                    id TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    error TEXT,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    next_attempt_at TEXT
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

                CREATE TABLE IF NOT EXISTS contact_profiles (
                    sender TEXT PRIMARY KEY,
                    display_name TEXT,
                    profile_picture_url TEXT,
                    profile_picture_path TEXT,
                    updated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS processed_messages (
                    message_id TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    status TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    error TEXT
                );

                CREATE TABLE IF NOT EXISTS conversation_messages (
                    id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    state TEXT,
                    media_id TEXT,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT
                );

                CREATE TABLE IF NOT EXISTS pending_media (
                    message_id TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    file_name TEXT,
                    mimetype TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    staging_path TEXT NOT NULL,
                    created_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS media_records (
                    media_id TEXT PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    relative_path TEXT NOT NULL,
                    mimetype TEXT,
                    size_bytes INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    absolute_path TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_conversation_messages_sender_created
                    ON conversation_messages (sender, created_at);

                CREATE INDEX IF NOT EXISTS idx_pending_media_sender
                    ON pending_media (sender);
                """
            )
            self._ensure_column(
                connection=connection,
                table_name="processing_jobs",
                column_name="attempts",
                definition="INTEGER NOT NULL DEFAULT 0",
            )
            self._ensure_column(
                connection=connection,
                table_name="processing_jobs",
                column_name="next_attempt_at",
                definition="TEXT",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="contact_name",
                definition="TEXT",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="pending_media_id",
                definition="TEXT",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="allowed_option_ids",
                definition="TEXT NOT NULL DEFAULT '[]'",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="processed_interaction_ids",
                definition="TEXT NOT NULL DEFAULT '[]'",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="interactive_created_at",
                definition="REAL",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="created_at",
                definition="REAL",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="expires_at",
                definition="REAL",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="last_interaction_at",
                definition="REAL",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="origin",
                definition="TEXT",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="contact_id",
                definition="TEXT",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="greeting_sent",
                definition="INTEGER NOT NULL DEFAULT 0",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="expiry_warning_sent",
                definition="INTEGER NOT NULL DEFAULT 0",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="batch_filenames",
                definition="TEXT NOT NULL DEFAULT '[]'",
            )
            self._ensure_column(
                connection=connection,
                table_name="conversation_sessions",
                column_name="received_types",
                definition="TEXT NOT NULL DEFAULT '[]'",
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=15.0)
        connection.row_factory = sqlite3.Row
        # Espera ate 15s por um lock em vez de falhar na hora com "database is
        # locked"; synchronous=NORMAL e seguro e rapido sob WAL.
        connection.execute("PRAGMA busy_timeout=15000")
        connection.execute("PRAGMA synchronous=NORMAL")
        return connection

    def _decode_job_row(self, row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        data["payload"] = json.loads(str(data["payload"]))
        return data

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        column_name: str,
        definition: str,
    ) -> None:
        columns = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        if any(str(column["name"]) == column_name for column in columns):
            return

        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")

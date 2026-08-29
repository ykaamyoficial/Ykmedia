import asyncio
import time
from pathlib import Path

from app.models.message import MessageType, ReceivedMessage, Sender
from app.services.conversation_engine import ConversationEngine
from app.services.session_expiry_notifier import SessionExpiryNotifier
from app.services.session_store import SQLiteSessionStore
from app.services.storage_service import StorageService


class FakeEvolutionClient:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_text_message(self, recipient: str, text: str) -> dict[str, object]:
        self.sent.append((recipient, text))
        return {"status": "PENDING"}


def _engine_with_active_session(tmp_path: Path, expires_in: float) -> StorageService:
    storage = StorageService(database_path=tmp_path / "ykmedia.sqlite3")
    engine = ConversationEngine(session_store=SQLiteSessionStore(storage_service=storage))
    engine.handle(
        ReceivedMessage(
            message_id="IMG1",
            sender=Sender(remote_jid="556200000000@s.whatsapp.net"),
            message_type=MessageType.IMAGE,
            raw_type="imageMessage",
        )
    )
    session = engine.get_session("556200000000@s.whatsapp.net")
    assert session is not None
    session.expires_at = time.time() + expires_in
    engine._session_store.update("556200000000@s.whatsapp.net", session)
    return storage


def test_notifies_sessions_that_expire_soon(tmp_path: Path) -> None:
    storage = _engine_with_active_session(tmp_path, expires_in=120)
    client = FakeEvolutionClient()
    notifier = SessionExpiryNotifier(storage, client, warning_seconds=300)

    sent = asyncio.run(notifier.notify_due())

    assert sent == 1
    assert client.sent[0][0] == "556200000000@s.whatsapp.net"
    assert "expira em" in client.sent[0][1]

    # não avisa de novo
    assert asyncio.run(notifier.notify_due()) == 0


def test_does_not_notify_sessions_that_are_not_close_to_expiring(tmp_path: Path) -> None:
    storage = _engine_with_active_session(tmp_path, expires_in=1800)
    client = FakeEvolutionClient()
    notifier = SessionExpiryNotifier(storage, client, warning_seconds=300)

    assert asyncio.run(notifier.notify_due()) == 0

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models.download import DownloadedMedia
from app.models.message import MessageType, ReceivedMessage
from app.models.persistence import (
    ConversationMessageDirection,
    ConversationMessageRecord,
    ConversationMessageStatus,
)
from app.repositories.conversation_message_repository import SQLiteConversationMessageRepository
from app.repositories.media_repository import InMemoryMediaRepository
from app.repositories.processed_message_repository import InMemoryProcessedMessageRepository
from app.services.category_service import CategoryService
from app.services.conversation_engine import ConversationEngine
from app.services.file_storage import FileStorage
from app.services.message_pipeline import MessagePipeline
from app.services.receive_media_use_case import ReceiveMediaUseCase
from app.services.session_store import MemorySessionStore
from app.services.storage_service import StorageService


SIMULATION_ROOT = PROJECT_ROOT / "tmp-debug-flow" / "conversation-simulation"
SENDER_JID = "556299999999@s.whatsapp.net"


@dataclass(frozen=True, slots=True)
class SimulatedStep:
    actor: str
    text: str


class FakeDownloadManager:
    async def download(self, message: ReceivedMessage) -> DownloadedMedia:
        suffix = {
            MessageType.IMAGE: "jpg",
            MessageType.AUDIO: "mp3",
            MessageType.VIDEO: "mp4",
            MessageType.DOCUMENT: "pdf",
        }.get(message.message_type, "bin")
        original_name = message.media.file_name if message.media else None
        file_name = original_name or f"{message.message_id}.{suffix}"
        content = f"simulated-content:{message.message_id}:{file_name}".encode("utf-8")
        return DownloadedMedia(
            message_id=message.message_id,
            content=content,
            mimetype=message.media.mimetype if message.media else "application/octet-stream",
            size_bytes=len(content),
            file_name=file_name,
        )


def main() -> int:
    report = asyncio.run(run_simulation())
    print(report)
    return 0


async def run_simulation() -> str:
    _reset_simulation_folder()
    storage_service = StorageService(database_path=SIMULATION_ROOT / "data" / "ykmedia.sqlite3")
    conversation_messages = SQLiteConversationMessageRepository(storage_service=storage_service)
    media_repository = InMemoryMediaRepository()
    file_storage = FileStorage(root_directory=SIMULATION_ROOT / "media")
    conversation_engine = ConversationEngine(
        session_store=MemorySessionStore(),
        category_service=CategoryService(storage_service=storage_service),
    )
    pipeline = MessagePipeline(
        download_manager=FakeDownloadManager(),
        file_storage=file_storage,
        conversation_engine=conversation_engine,
        processed_message_repository=InMemoryProcessedMessageRepository(),
    )
    use_case = ReceiveMediaUseCase(
        message_pipeline=pipeline,
        media_repository=media_repository,
        conversation_message_repository=conversation_messages,
        media_history_recorder=storage_service,
        file_storage=file_storage,
        media_grouping_window_seconds=0.2,
    )

    steps: list[SimulatedStep] = []

    _seed_old_contact(conversation_messages)
    await _send(use_case, steps, "Henrique", "Oi, posso mandar arquivo?", _text_payload("INFO1", "Oi, posso mandar arquivo?"))

    await _send(
        use_case,
        steps,
        "Henrique",
        "[imagem] foto_culto.jpg",
        _media_payload("IMG1", "imageMessage", "image/jpeg", "foto_culto.jpg"),
    )
    await _send(use_case, steps, "Henrique", "1", _text_payload("CAT1", "1"))
    await _send(use_case, steps, "Henrique", "2", _text_payload("DECIDE1", "2"))
    await _send(use_case, steps, "Henrique", "Entrada do culto", _text_payload("NAME1", "Entrada do culto"))

    await _send_media_batch(
        use_case=use_case,
        steps=steps,
        sender_name="Wilson",
        items=[
            (
                "[video] abertura.mp4",
                _media_payload("VID1", "videoMessage", "video/mp4", "abertura.mp4", remote_jid="556288888888@s.whatsapp.net"),
            ),
            (
                "[audio] fundo.mp3",
                _media_payload("AUD2", "audioMessage", "audio/mpeg", "fundo.mp3", remote_jid="556288888888@s.whatsapp.net"),
            ),
            (
                "[documento] escala.pdf",
                _media_payload("DOC3", "documentMessage", "application/pdf", "escala.pdf", remote_jid="556288888888@s.whatsapp.net"),
            ),
        ],
    )
    await _send(use_case, steps, "Wilson", "2", _text_payload("CAT2", "2", remote_jid="556288888888@s.whatsapp.net"))

    return _format_report(
        steps=steps,
        media_root=SIMULATION_ROOT / "media",
        media_history=storage_service.list_media_history(),
        contacts=storage_service.list_media_contacts(),
    )


async def _send(
    use_case: ReceiveMediaUseCase,
    steps: list[SimulatedStep],
    sender_name: str,
    visible_message: str,
    payload: dict[str, Any],
) -> None:
    steps.append(SimulatedStep(sender_name, visible_message))
    result = await use_case.execute(payload)
    if result.next_message:
        steps.append(SimulatedStep("YkMedia", result.next_message))


async def _send_media_batch(
    use_case: ReceiveMediaUseCase,
    steps: list[SimulatedStep],
    sender_name: str,
    items: list[tuple[str, dict[str, Any]]],
) -> None:
    if not items:
        return

    visible_message, payload = items[0]
    steps.append(SimulatedStep(sender_name, visible_message))
    first_task = asyncio.create_task(use_case.execute(payload))

    for visible_message, payload in items[1:]:
        await asyncio.sleep(0.01)
        steps.append(SimulatedStep(sender_name, visible_message))
        result = await use_case.execute(payload)
        if result.next_message:
            steps.append(SimulatedStep("YkMedia", result.next_message))

    first_result = await first_task
    if first_result.next_message:
        steps.append(SimulatedStep("YkMedia", first_result.next_message))


def _seed_old_contact(repository: SQLiteConversationMessageRepository) -> None:
    repository.save(
        ConversationMessageRecord(
            id="seed-old-contact",
            message_id="OLD1",
            sender=SENDER_JID,
            direction=ConversationMessageDirection.INBOUND,
            content="Oi",
            message_type="texto",
            state="IDLE",
            media_id=None,
            created_at=(datetime.now(timezone.utc) - timedelta(days=1, minutes=5)).isoformat(timespec="seconds"),
            status=ConversationMessageStatus.RECEIVED,
        )
    )


def _payload_base(message_id: str, message: dict[str, Any], remote_jid: str = SENDER_JID) -> dict[str, Any]:
    push_name = "Wilson" if remote_jid.startswith("556288888888") else "Henrique"
    return {
        "event": "messages.upsert",
        "data": {
            "key": {
                "id": message_id,
                "remoteJid": remote_jid,
                "fromMe": False,
            },
            "pushName": push_name,
            "message": message,
        },
    }


def _text_payload(message_id: str, text: str, remote_jid: str = SENDER_JID) -> dict[str, Any]:
    return _payload_base(message_id, {"conversation": text}, remote_jid=remote_jid)


def _media_payload(
    message_id: str,
    raw_type: str,
    mimetype: str,
    file_name: str,
    remote_jid: str = SENDER_JID,
) -> dict[str, Any]:
    return _payload_base(
        message_id,
        {
            raw_type: {
                "mimetype": mimetype,
                "fileName": file_name,
                "mediaKey": f"fake-key-{message_id}",
                "directPath": f"/fake/{message_id}",
            }
        },
        remote_jid=remote_jid,
    )


def _format_report(
    steps: list[SimulatedStep],
    media_root: Path,
    media_history: list[dict[str, Any]],
    contacts: list[dict[str, Any]],
) -> str:
    lines = [
        "SIMULACAO REALISTA DO FLUXO YKMEDIA",
        "=" * 42,
        "",
        "CONVERSA NO WHATSAPP",
        "-" * 42,
    ]
    for index, step in enumerate(steps, start=1):
        lines.append(f"{index:02d}. {step.actor}:")
        lines.extend(f"    {line}" for line in step.text.splitlines())
        lines.append("")

    lines.extend(
        [
            "PASTAS E ARQUIVOS CRIADOS",
            "-" * 42,
        ]
    )
    created_files = [path for path in sorted(media_root.rglob("*")) if path.is_file()]
    if not created_files:
        lines.append("Nenhum arquivo criado.")
    for path in created_files:
        lines.append(f"- {path.relative_to(media_root)}")

    lines.extend(
        [
            "",
            "HISTORICO GRAVADO NO SQLITE TEMPORARIO",
            "-" * 42,
        ]
    )
    for item in media_history:
        lines.append(
            "- "
            f"{item['sender']} | {item['category']} | {item['final_name']} | "
            f"{item['file_path']} | {item['status']}"
        )

    lines.extend(
        [
            "",
            "CONTATOS QUE A INTERFACE DEVE ENXERGAR",
            "-" * 42,
        ]
    )
    for contact in contacts:
        lines.append(
            "- "
            f"{contact['sender']} | {contact['media_count']} arquivo(s) | "
            f"ultimo: {contact['last_media']}"
        )

    lines.extend(
        [
            "",
            f"Ambiente temporario: {SIMULATION_ROOT}",
        ]
    )
    return "\n".join(lines)


def _reset_simulation_folder() -> None:
    if SIMULATION_ROOT.exists():
        shutil.rmtree(SIMULATION_ROOT)
    (SIMULATION_ROOT / "media").mkdir(parents=True, exist_ok=True)
    (SIMULATION_ROOT / "data").mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())

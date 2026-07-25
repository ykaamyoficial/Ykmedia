import logging
from typing import Any

logger = logging.getLogger(__name__)


def _event_name(payload: dict[str, Any]) -> str:
    return str(payload.get("event") or "").strip().lower()


async def process_evolution_event(payload: dict[str, Any]) -> dict[str, object]:
    event = _event_name(payload)

    if event not in {"messages.upsert", "messages_upsert"}:
        return {"processed": False, "reason": "evento_ignorado", "event": event}

    data = payload.get("data") or {}
    key = data.get("key") or {}

    # Ignora mensagens enviadas pelo próprio número conectado.
    if bool(key.get("fromMe")):
        return {"processed": False, "reason": "mensagem_propria"}

    message_id = str(key.get("id") or "")
    remote_jid = str(key.get("remoteJid") or "")
    message = data.get("message") or {}

    message_type = next(iter(message), "unknown") if isinstance(message, dict) else "unknown"

    logger.info(
        "Mensagem recebida: id=%s contato=%s tipo=%s",
        message_id,
        remote_jid,
        message_type,
    )

    # Nesta primeira etapa apenas recebemos e classificamos o evento.
    # O download e a conversa automática entram nas próximas etapas.
    return {
        "processed": True,
        "message_id": message_id,
        "remote_jid": remote_jid,
        "message_type": message_type,
    }

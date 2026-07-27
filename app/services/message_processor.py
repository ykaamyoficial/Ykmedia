import logging
from dataclasses import dataclass
from enum import StrEnum

from app.models.message import MessageType, ReceivedMessage
from app.services.evolution_message_mapper import EvolutionMessageMappingResult

logger = logging.getLogger(__name__)


class MessageAction(StrEnum):
    IGNORE = "ignorar"
    ASK_CLASSIFICATION = "solicitar_classificacao"


@dataclass(frozen=True, slots=True)
class ProcessingDecision:
    action: MessageAction
    response: str


def process_mapping_result(mapping_result: EvolutionMessageMappingResult) -> dict[str, object]:
    if mapping_result.is_ignored:
        result: dict[str, object] = {
            "processed": False,
            "reason": mapping_result.ignored_reason or "mensagem_invalida",
        }

        if mapping_result.event is not None:
            result["event"] = mapping_result.event

        return result

    message = mapping_result.message
    if message is None:
        return {"processed": False, "reason": "mensagem_invalida"}

    return process_received_message(message)


def process_received_message(message: ReceivedMessage) -> dict[str, object]:
    decision = process_message(message)
    return _build_result(message, decision)


def process_message(message: ReceivedMessage) -> ProcessingDecision:
    return _decide_action(message)


def is_command_message(message: ReceivedMessage) -> bool:
    return bool(message.text and message.text.strip().startswith("!"))


def _decide_action(message: ReceivedMessage) -> ProcessingDecision:
    if message.message_type is MessageType.UNKNOWN:
        return ProcessingDecision(
            action=MessageAction.IGNORE,
            response="Tipo de mensagem nao suportado nesta etapa.",
        )

    return ProcessingDecision(
        action=MessageAction.ASK_CLASSIFICATION,
        response="Mensagem recebida e pronta para classificacao.",
    )


def _build_result(message: ReceivedMessage, decision: ProcessingDecision) -> dict[str, object]:
    logger.info(
        "Mensagem recebida: id=%s contato=%s tipo=%s acao=%s",
        message.message_id,
        message.sender.remote_jid,
        message.message_type.value,
        decision.action.value,
    )

    return {
        "processed": True,
        "message_id": message.message_id,
        "remote_jid": message.sender.remote_jid,
        "message_type": message.raw_type,
        "message_kind": message.message_type.value,
        "action": decision.action.value,
        "response": decision.response,
    }

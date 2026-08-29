import unicodedata
from dataclasses import dataclass

from app.models.message import ReceivedMessage
from app.services.conversation_engine import ConversationEngine
from app.services.message_catalog import WhatsAppMessageCatalog

_ALIASES = {
    "ajuda": "ajuda",
    "menu": "ajuda",
    "cancelar": "cancelar",
    "status": "status",
    "recomecar": "reiniciar",
    "reiniciar": "reiniciar",
    "versao": "versao",
}


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: str
    response: str


class CommandProcessor:
    def __init__(self, conversation_engine: ConversationEngine) -> None:
        self._conversation_engine = conversation_engine

    def process(self, message: ReceivedMessage) -> CommandResult:
        command = self._normalize_command(message.text)

        if command == "ajuda":
            return CommandResult(command=command, response=WhatsAppMessageCatalog.command_help())

        if command == "cancelar":
            self._conversation_engine.reset(message.sender.remote_jid)
            return CommandResult(command=command, response=WhatsAppMessageCatalog.command_cancelled())

        if command == "status":
            session = self._conversation_engine.get_session(message.sender.remote_jid)
            if session is None:
                return CommandResult(
                    command=command,
                    response=WhatsAppMessageCatalog.command_no_active_conversation(),
                )
            return CommandResult(
                command=command,
                response=WhatsAppMessageCatalog.command_status(session.state.value),
            )

        if command == "reiniciar":
            self._conversation_engine.reset(message.sender.remote_jid)
            return CommandResult(command=command, response=WhatsAppMessageCatalog.command_restarted())

        if command == "versao":
            return CommandResult(command=command, response=WhatsAppMessageCatalog.command_version())

        return CommandResult(command=command, response=WhatsAppMessageCatalog.command_unknown())

    def _normalize_command(self, text: str | None) -> str:
        raw = (text or "").strip().lstrip("!").lower().split(maxsplit=1)
        word = _strip_accents(raw[0]) if raw else ""
        return _ALIASES.get(word, word)


def _strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )

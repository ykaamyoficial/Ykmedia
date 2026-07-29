from dataclasses import dataclass

from app.models.message import ReceivedMessage
from app.services.conversation_engine import ConversationEngine
from app.services.message_catalog import WhatsAppMessageCatalog


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: str
    response: str


class CommandProcessor:
    def __init__(self, conversation_engine: ConversationEngine) -> None:
        self._conversation_engine = conversation_engine

    def process(self, message: ReceivedMessage) -> CommandResult:
        command = self._normalize_command(message.text)

        if command == "!ajuda":
            return CommandResult(command=command, response=self._help_message())

        if command == "!cancelar":
            self._conversation_engine.reset(message.sender.remote_jid)
            return CommandResult(command=command, response=WhatsAppMessageCatalog.command_cancelled())

        if command == "!status":
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

        if command == "!reiniciar":
            self._conversation_engine.reset(message.sender.remote_jid)
            return CommandResult(command=command, response=WhatsAppMessageCatalog.command_restarted())

        if command == "!versao":
            return CommandResult(
                command=command,
                response=WhatsAppMessageCatalog.command_version(),
            )

        return CommandResult(
            command=command,
            response=WhatsAppMessageCatalog.command_unknown(),
        )

    def _normalize_command(self, text: str | None) -> str:
        return (text or "").strip().lower().split(maxsplit=1)[0]

    def _help_message(self) -> str:
        return WhatsAppMessageCatalog.command_help()

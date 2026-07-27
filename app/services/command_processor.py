from dataclasses import dataclass

from app.core.config import settings
from app.models.message import ReceivedMessage
from app.services.conversation_engine import ConversationEngine


@dataclass(frozen=True, slots=True)
class CommandResult:
    command: str
    response: str


class CommandProcessor:
    _AVAILABLE_COMMANDS = {
        "!ajuda": "Lista os comandos disponiveis.",
        "!cancelar": "Cancela a conversa atual.",
        "!status": "Mostra o estado atual da conversa.",
        "!reiniciar": "Reinicia completamente a conversa.",
        "!versao": "Exibe a versao do YkMedia.",
    }

    def __init__(self, conversation_engine: ConversationEngine) -> None:
        self._conversation_engine = conversation_engine

    def process(self, message: ReceivedMessage) -> CommandResult:
        command = self._normalize_command(message.text)

        if command == "!ajuda":
            return CommandResult(command=command, response=self._help_message())

        if command == "!cancelar":
            self._conversation_engine.reset(message.sender.remote_jid)
            return CommandResult(command=command, response="Conversa cancelada.")

        if command == "!status":
            session = self._conversation_engine.get_session(message.sender.remote_jid)
            if session is None:
                return CommandResult(command=command, response="Nao ha conversa ativa.")

            return CommandResult(
                command=command,
                response=f"Estado atual da conversa: {session.state.value}.",
            )

        if command == "!reiniciar":
            self._conversation_engine.reset(message.sender.remote_jid)
            return CommandResult(command=command, response="Conversa reiniciada.")

        if command == "!versao":
            return CommandResult(
                command=command,
                response=f"YkMedia {settings.APP_VERSION}",
            )

        return CommandResult(
            command=command,
            response="Comando nao reconhecido. Envie !ajuda para ver os comandos disponiveis.",
        )

    def _normalize_command(self, text: str | None) -> str:
        return (text or "").strip().lower().split(maxsplit=1)[0]

    def _help_message(self) -> str:
        command_lines = [
            f"{command} - {description}"
            for command, description in self._AVAILABLE_COMMANDS.items()
        ]
        return "Comandos disponiveis:\n" + "\n".join(command_lines)

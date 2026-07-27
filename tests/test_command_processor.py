from app.models.message import MessageType, ReceivedMessage, Sender
from app.services.command_processor import CommandProcessor
from app.services.conversation_engine import ConversationEngine, ConversationState
from app.services.session_store import MemorySessionStore


def _message(text: str, remote_jid: str = "556299999999@s.whatsapp.net") -> ReceivedMessage:
    return ReceivedMessage(
        message_id="MSG1",
        sender=Sender(remote_jid=remote_jid),
        message_type=MessageType.TEXT,
        raw_type="conversation",
        text=text,
    )


def test_help_command_lists_all_commands() -> None:
    processor = CommandProcessor(ConversationEngine(session_store=MemorySessionStore()))

    result = processor.process(_message("!ajuda"))

    assert result.command == "!ajuda"
    assert "!ajuda" in result.response
    assert "!cancelar" in result.response
    assert "!status" in result.response
    assert "!reiniciar" in result.response
    assert "!versao" in result.response


def test_cancel_command_removes_active_conversation() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    processor = CommandProcessor(engine)
    engine.handle(_message("arquivo"))

    result = processor.process(_message("!cancelar"))

    assert result.response == "Conversa cancelada."
    assert engine.get_session("556299999999@s.whatsapp.net") is None


def test_status_command_with_active_conversation() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    processor = CommandProcessor(engine)
    engine.handle(_message("arquivo"))

    result = processor.process(_message("!status"))

    assert "WAITING_CATEGORY" in result.response


def test_status_command_without_active_conversation() -> None:
    processor = CommandProcessor(ConversationEngine(session_store=MemorySessionStore()))

    result = processor.process(_message("!status"))

    assert result.response == "Nao ha conversa ativa."


def test_restart_command_removes_active_conversation() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    processor = CommandProcessor(engine)
    engine.handle(_message("arquivo"))

    result = processor.process(_message("!reiniciar"))

    assert result.response == "Conversa reiniciada."
    assert engine.get_session("556299999999@s.whatsapp.net") is None


def test_version_command() -> None:
    processor = CommandProcessor(ConversationEngine(session_store=MemorySessionStore()))

    result = processor.process(_message("!versao"))

    assert result.command == "!versao"
    assert result.response.startswith("YkMedia ")


def test_unknown_command() -> None:
    processor = CommandProcessor(ConversationEngine(session_store=MemorySessionStore()))

    result = processor.process(_message("!naoexiste"))

    assert result.command == "!naoexiste"
    assert "Comando nao reconhecido" in result.response


def test_command_during_active_conversation_does_not_advance_state() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    processor = CommandProcessor(engine)
    engine.handle(_message("arquivo"))

    result = processor.process(_message("!status"))

    session = engine.get_session("556299999999@s.whatsapp.net")
    assert session is not None
    assert session.state is ConversationState.WAITING_CATEGORY
    assert "WAITING_CATEGORY" in result.response

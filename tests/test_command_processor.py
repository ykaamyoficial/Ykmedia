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


def _media_message(remote_jid: str = "556299999999@s.whatsapp.net") -> ReceivedMessage:
    return ReceivedMessage(
        message_id="MSG-MEDIA",
        sender=Sender(remote_jid=remote_jid),
        message_type=MessageType.IMAGE,
        raw_type="imageMessage",
    )


def test_help_command_lists_all_commands() -> None:
    processor = CommandProcessor(ConversationEngine(session_store=MemorySessionStore()))

    result = processor.process(_message("ajuda"))

    assert result.command == "ajuda"
    for word in ("ajuda", "status", "recomeçar", "cancelar"):
        assert word in result.response


def test_bang_prefix_still_works() -> None:
    processor = CommandProcessor(ConversationEngine(session_store=MemorySessionStore()))

    assert processor.process(_message("!ajuda")).command == "ajuda"


def test_cancel_command_removes_active_conversation() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    processor = CommandProcessor(engine)
    engine.handle(_media_message())

    result = processor.process(_message("cancelar"))

    assert "descartados" in result.response
    assert engine.get_session("556299999999@s.whatsapp.net") is None


def test_status_command_with_active_conversation() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    processor = CommandProcessor(engine)
    engine.handle(_media_message())

    result = processor.process(_message("status"))

    assert "categoria" in result.response.lower()


def test_status_command_without_active_conversation() -> None:
    processor = CommandProcessor(ConversationEngine(session_store=MemorySessionStore()))

    result = processor.process(_message("status"))

    assert "não tem nenhuma conversa" in result.response


def test_restart_command_removes_active_conversation() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    processor = CommandProcessor(engine)
    engine.handle(_media_message())

    result = processor.process(_message("recomeçar"))

    assert "reiniciada" in result.response
    assert engine.get_session("556299999999@s.whatsapp.net") is None


def test_version_command() -> None:
    processor = CommandProcessor(ConversationEngine(session_store=MemorySessionStore()))

    result = processor.process(_message("!versao"))

    assert result.command == "versao"
    assert result.response.startswith("YkMedia ")


def test_unknown_command() -> None:
    processor = CommandProcessor(ConversationEngine(session_store=MemorySessionStore()))

    result = processor.process(_message("!naoexiste"))

    assert result.command == "naoexiste"
    assert "Não reconheci" in result.response


def test_command_during_active_conversation_does_not_advance_state() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    processor = CommandProcessor(engine)
    engine.handle(_media_message())

    processor.process(_message("status"))

    session = engine.get_session("556299999999@s.whatsapp.net")
    assert session is not None
    assert session.state is ConversationState.WAITING_CATEGORY_SELECTION

from app.models.message import MessageType, ReceivedMessage, Sender
from app.services.category_service import CategoryService
from app.services.conversation_engine import ConversationEngine, ConversationState
from app.services.session_store import MemorySessionStore


def _message(text: str | None = None, remote_jid: str = "556299999999@s.whatsapp.net") -> ReceivedMessage:
    return ReceivedMessage(
        message_id="MSG1",
        sender=Sender(remote_jid=remote_jid),
        message_type=MessageType.TEXT if text is not None else MessageType.AUDIO,
        raw_type="conversation" if text is not None else "audioMessage",
        text=text,
    )


def test_starts_conversation() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    result = engine.handle(_message())

    assert result.current_state is ConversationState.IDLE
    assert result.next_state is ConversationState.WAITING_USAGE_CONFIRMATION
    assert result.is_finished is False
    assert "sonoplastia" in result.suggested_response


def test_transitions_between_states() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    engine.handle(_message())
    confirmation_result = engine.handle(_message("1"))
    category_result = engine.handle(_message("1"))
    filename_result = engine.handle(_message("louvor"))

    assert confirmation_result.current_state is ConversationState.WAITING_USAGE_CONFIRMATION
    assert confirmation_result.next_state is ConversationState.WAITING_CATEGORY
    assert category_result.current_state is ConversationState.WAITING_CATEGORY
    assert category_result.next_state is ConversationState.WAITING_FILENAME
    assert filename_result.current_state is ConversationState.WAITING_FILENAME
    assert filename_result.next_state is ConversationState.FINISHED
    assert filename_result.is_finished is True


def test_keeps_state_on_invalid_category_response() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    engine.handle(_message())
    engine.handle(_message("1"))
    result = engine.handle(_message("9"))

    assert result.current_state is ConversationState.WAITING_CATEGORY
    assert result.next_state is ConversationState.WAITING_CATEGORY
    assert result.is_finished is False
    assert "Opcao invalida" in result.suggested_response


def test_finishes_flow() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    engine.handle(_message())
    engine.handle(_message("1"))
    engine.handle(_message("1"))
    result = engine.handle(_message("louvor"))

    assert result.current_state is ConversationState.WAITING_FILENAME
    assert result.next_state is ConversationState.FINISHED
    assert result.is_finished is True


def test_restarts_conversation_after_reset() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    remote_jid = "556299999999@s.whatsapp.net"

    engine.handle(_message(remote_jid=remote_jid))
    engine.handle(_message("1", remote_jid=remote_jid))
    engine.handle(_message("1", remote_jid=remote_jid))
    engine.reset(remote_jid)
    result = engine.handle(_message(remote_jid=remote_jid))

    assert result.current_state is ConversationState.IDLE
    assert result.next_state is ConversationState.WAITING_USAGE_CONFIRMATION


def test_starts_new_flow_when_new_media_arrives_after_finished_flow() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    engine.handle(_message())
    engine.handle(_message("1"))
    engine.handle(_message("1"))
    engine.handle(_message("louvor"))
    result = engine.handle(_message())

    assert result.current_state is ConversationState.IDLE
    assert result.next_state is ConversationState.WAITING_USAGE_CONFIRMATION
    assert result.is_finished is False


def test_cancels_when_usage_is_rejected() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    engine.handle(_message())
    result = engine.handle(_message("2"))

    assert result.current_state is ConversationState.WAITING_USAGE_CONFIRMATION
    assert result.next_state is ConversationState.FINISHED
    assert result.is_finished is True
    assert "nao sera enviado" in result.suggested_response


def test_uses_dynamic_categories() -> None:
    category_service = CategoryService(categories=["Eventos", "Ensaios"])
    engine = ConversationEngine(
        session_store=MemorySessionStore(),
        category_service=category_service,
    )

    start_result = engine.handle(_message())
    confirmation_result = engine.handle(_message("1"))
    category_result = engine.handle(_message("2"))
    session = engine.get_session("556299999999@s.whatsapp.net")

    assert "sonoplastia" in start_result.suggested_response
    assert "1 Eventos, 2 Ensaios" in confirmation_result.suggested_response
    assert category_result.next_state is ConversationState.WAITING_FILENAME
    assert session is not None
    assert session.category == "Ensaios"

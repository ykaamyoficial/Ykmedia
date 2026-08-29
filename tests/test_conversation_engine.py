from app.models.message import Media, MessageType, ReceivedMessage, Sender
from app.models.interactive import IncomingInteraction, InteractionSource
from app.services.category_service import CategoryService
from app.services.conversation_engine import ConversationEngine, ConversationState
from app.services.session_store import MemorySessionStore


def _message(
    text: str | None = None,
    message_type: MessageType = MessageType.TEXT,
    remote_jid: str = "556299999999@s.whatsapp.net",
    raw_type: str | None = None,
) -> ReceivedMessage:
    return ReceivedMessage(
        message_id=f"MSG-{text or message_type.value}",
        sender=Sender(remote_jid=remote_jid, is_group=remote_jid.endswith("@g.us")),
        message_type=message_type,
        raw_type=raw_type or ("conversation" if message_type is MessageType.TEXT else f"{message_type.value}Message"),
        text=text,
        media=Media(mimetype="image/jpeg") if message_type is not MessageType.TEXT else None,
    )


def _start_media_flow(
    engine: ConversationEngine,
    message_type: MessageType = MessageType.IMAGE,
    raw_type: str = "imageMessage",
):
    """Envia uma mídia e conclui a coleta, deixando a sessão em AGUARDANDO_CATEGORIA."""
    start = engine.handle(_message(message_type=message_type, raw_type=raw_type))
    engine.handle(_message("concluir"))
    return start


def _interaction_message(option_id: str, title: str = "Opcao") -> ReceivedMessage:
    return ReceivedMessage(
        message_id=f"MSG-{option_id}",
        sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
        message_type=MessageType.TEXT,
        raw_type="buttonsResponseMessage",
        text=title,
        interaction=IncomingInteraction(
            option_id=option_id,
            option_title=title,
            source_type=InteractionSource.BUTTON_REPLY,
        ),
    )


def test_text_simple_is_ignored_without_starting_session() -> None:
    store = MemorySessionStore()
    engine = ConversationEngine(session_store=store)

    result = engine.handle(_message("Ola"))

    assert result.current_state is ConversationState.IDLE
    assert result.next_state is ConversationState.IDLE
    assert result.suggested_response == ""
    assert store.exists("556299999999@s.whatsapp.net") is False


def test_group_message_is_ignored() -> None:
    store = MemorySessionStore()
    engine = ConversationEngine(session_store=store)

    result = engine.handle(
        _message(
            message_type=MessageType.IMAGE,
            remote_jid="556299999999-123@g.us",
            raw_type="imageMessage",
        )
    )

    assert result.suggested_response == ""
    assert result.next_state is ConversationState.IDLE


def test_sticker_is_ignored() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    result = engine.handle(_message(message_type=MessageType.STICKER, raw_type="stickerMessage"))

    assert result.next_state is ConversationState.IDLE
    assert result.suggested_response == ""


def test_image_starts_conversation_with_single_question() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    result = engine.handle(_message(message_type=MessageType.IMAGE, raw_type="imageMessage"))

    assert result.current_state is ConversationState.IDLE
    assert result.next_state is ConversationState.WAITING_MEDIA
    assert result.is_finished is False
    assert "Recebi *1 arquivo*" in result.suggested_response
    assert "Concluir envio" in result.suggested_response
    assert "cancelar" in result.suggested_response
    assert result.interactive_prompt is not None

    after_done = engine.handle(_message("concluir"))
    assert after_done.next_state is ConversationState.WAITING_CATEGORY_SELECTION
    assert "Passo 1 de 3" in after_done.suggested_response


def test_greeting_uses_the_contact_first_name() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    message = ReceivedMessage(
        message_id="IMG1",
        sender=Sender(remote_jid="556200000000@s.whatsapp.net", display_name="Marina Souza"),
        message_type=MessageType.IMAGE,
        raw_type="imageMessage",
    )

    result = engine.handle(message)

    assert "Olá, Marina!" in result.suggested_response
    session = engine.get_session(message.sender.remote_jid)
    assert session is not None and session.contact_name == "Marina"


def test_valid_link_starts_conversation() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    result = engine.handle(_message("https://youtu.be/abc", MessageType.LINK, raw_type="youtubeMessage"))

    assert result.next_state is ConversationState.WAITING_MEDIA
    assert "Recebi *1 arquivo*" in result.suggested_response
    after_done = engine.handle(_message("concluir"))
    assert after_done.next_state is ConversationState.WAITING_CATEGORY_SELECTION
    assert "Passo 1 de 3" in after_done.suggested_response


def test_multiple_files_are_grouped_in_same_session() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    start = engine.handle(_message(message_type=MessageType.VIDEO, raw_type="videoMessage"))
    second = engine.handle(_message(message_type=MessageType.IMAGE, raw_type="imageMessage"))
    session = engine.get_session("556299999999@s.whatsapp.net")

    assert start.suggested_response
    assert second.suggested_response == ""
    assert session is not None
    assert session.received_types == ("video", "imagem")


def test_single_file_asks_if_user_wants_to_rename_after_category() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    _start_media_flow(engine)
    result = engine.handle(_message("1"))
    session = engine.get_session("556299999999@s.whatsapp.net")

    assert result.current_state is ConversationState.WAITING_CATEGORY_SELECTION
    assert result.next_state is ConversationState.WAITING_FILENAME_DECISION
    assert result.is_finished is False
    assert "Passo 2 de 3" in result.suggested_response
    assert "Manter o nome original" in result.suggested_response
    assert session is not None
    assert session.category == "Louvores"


def test_keep_original_name_goes_to_confirmation_then_finishes() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    _start_media_flow(engine)
    engine.handle(_message("1"))
    confirmation = engine.handle(_message("1"))
    result = engine.handle(_message("confirmar"))

    assert confirmation.next_state is ConversationState.WAITING_CONFIRMATION
    assert "Passo 3 de 3" in confirmation.suggested_response
    assert "Louvores" in confirmation.suggested_response
    assert result.current_state is ConversationState.WAITING_CONFIRMATION
    assert result.next_state is ConversationState.FINISHED
    assert result.is_finished is True
    assert "salvo em *Louvores*" in result.suggested_response


def test_collecting_state_absorbs_media_until_concluir() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    engine.handle(_message(message_type=MessageType.IMAGE, raw_type="imageMessage"))
    second = engine.handle(_message(message_type=MessageType.AUDIO, raw_type="audioMessage"))
    nudge = engine.handle(_message("qualquer coisa"))
    done = engine.handle(_message("concluir"))
    session = engine.get_session("556299999999@s.whatsapp.net")

    assert second.suggested_response == ""
    assert second.next_state is ConversationState.WAITING_MEDIA
    assert "Concluir envio" in nudge.suggested_response
    assert done.next_state is ConversationState.WAITING_CATEGORY_SELECTION
    assert session is not None and session.received_types == ("imagem", "audio")


def test_batch_offers_auto_number_or_one_by_one() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    engine.handle(_message(message_type=MessageType.IMAGE, raw_type="imageMessage"))
    engine.handle(_message(message_type=MessageType.AUDIO, raw_type="audioMessage"))
    engine.handle(_message("concluir"))
    result = engine.handle(_message("1"))

    assert result.next_state is ConversationState.WAITING_FILENAME_DECISION
    assert "Passo 2 de 3 · Nomes" in result.suggested_response
    assert result.interactive_prompt is not None
    assert [option.id for option in result.interactive_prompt.options] == [
        "filename:auto_number",
        "filename:one_by_one",
    ]


def test_batch_named_one_by_one_collects_every_name() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    engine.handle(_message(message_type=MessageType.IMAGE, raw_type="imageMessage"))
    engine.handle(_message(message_type=MessageType.AUDIO, raw_type="audioMessage"))
    engine.handle(_message("concluir"))
    engine.handle(_message("1"))
    first_ask = engine.handle(_message("2"))
    second_ask = engine.handle(_message("Abertura"))
    confirmation = engine.handle(_message("Louvor"))
    session = engine.get_session("556299999999@s.whatsapp.net")

    assert "Arquivo 1 de 2" in first_ask.suggested_response
    assert "Arquivo 2 de 2" in second_ask.suggested_response
    assert confirmation.next_state is ConversationState.WAITING_CONFIRMATION
    assert session is not None
    assert session.batch_filenames == ("Abertura", "Louvor")


def test_invalid_filename_is_rejected_without_advancing() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    _start_media_flow(engine)
    engine.handle(_message("1"))
    engine.handle(_message("2"))

    result = engine.handle(_message("pasta/arquivo"))

    assert result.next_state is ConversationState.WAITING_CUSTOM_FILENAME
    assert "não pode ser usado" in result.suggested_response


def test_confirmation_cancel_resets_session() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    _start_media_flow(engine)
    engine.handle(_message("1"))
    engine.handle(_message("1"))

    result = engine.handle(_message("cancelar"))

    assert result.next_state is ConversationState.IDLE
    assert result.is_finished is True
    assert engine.get_session("556299999999@s.whatsapp.net") is None


def test_confirmation_correct_returns_to_category() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    _start_media_flow(engine)
    engine.handle(_message("1"))
    engine.handle(_message("1"))

    result = engine.handle(_message("corrigir"))
    session = engine.get_session("556299999999@s.whatsapp.net")

    assert result.next_state is ConversationState.WAITING_CATEGORY_SELECTION
    assert session is not None and session.category is None


def test_invalid_category_keeps_state() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    _start_media_flow(engine)
    result = engine.handle(_message("9"))

    assert result.current_state is ConversationState.WAITING_CATEGORY_SELECTION
    assert result.next_state is ConversationState.WAITING_CATEGORY_SELECTION
    assert result.is_finished is False
    assert "Não encontrei essa opção" in result.suggested_response


def test_timeout_cancels_session() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())
    engine.handle(_message(message_type=MessageType.IMAGE, raw_type="imageMessage"))
    session = engine.get_session("556299999999@s.whatsapp.net")
    assert session is not None
    session.expires_at = 1

    result = engine.handle(_message("1"))

    assert result.next_state is ConversationState.IDLE
    assert result.is_finished is True
    assert "expirou por inatividade" in result.suggested_response
    assert engine.get_session("556299999999@s.whatsapp.net") is None


def test_restarts_new_session_after_finished_flow() -> None:
    engine = ConversationEngine(session_store=MemorySessionStore())

    _start_media_flow(engine)
    engine.handle(_message("1"))
    engine.handle(_message("1"))
    engine.handle(_message("confirmar"))
    result = engine.handle(_message(message_type=MessageType.AUDIO, raw_type="audioMessage"))

    assert result.current_state is ConversationState.IDLE
    assert result.next_state is ConversationState.WAITING_MEDIA


def test_uses_dynamic_categories() -> None:
    category_service = CategoryService(categories=["Eventos", "Ensaios"])
    engine = ConversationEngine(
        session_store=MemorySessionStore(),
        category_service=category_service,
    )

    engine.handle(_message(message_type=MessageType.IMAGE, raw_type="imageMessage"))
    category_prompt = engine.handle(_message("concluir"))
    category_result = engine.handle(_message("2"))
    session = engine.get_session("556299999999@s.whatsapp.net")

    assert "1 - Eventos" in category_prompt.suggested_response
    assert "2 - Ensaios" in category_prompt.suggested_response
    assert category_result.next_state is ConversationState.WAITING_FILENAME_DECISION
    assert session is not None
    assert session.category == "Ensaios"


def test_selects_category_from_interactive_button() -> None:
    engine = ConversationEngine(
        session_store=MemorySessionStore(),
        category_service=CategoryService(categories=["Louvores", "Mensagens"]),
    )

    _start_media_flow(engine)
    result = engine.handle(_interaction_message("category:2", "Mensagens"))
    session = engine.get_session("556299999999@s.whatsapp.net")

    assert result.next_state is ConversationState.WAITING_FILENAME_DECISION
    assert session is not None
    assert session.category == "Mensagens"
    assert result.interactive_prompt is not None
    assert [option.id for option in result.interactive_prompt.options] == [
        "filename:keep_original",
        "filename:custom",
    ]

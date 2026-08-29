from app.models.message import MessageType, ReceivedMessage, Sender
from app.services.evolution_message_mapper import EvolutionMessageMappingResult
from app.services.message_processor import (
    is_command_message,
    process_mapping_result,
    process_received_message,
)


def test_processes_text_message() -> None:
    result = process_received_message(
        ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.TEXT,
            raw_type="conversation",
            text="Ola",
        )
    )

    assert result["processed"] is True
    assert result["message_type"] == "conversation"
    assert result["message_kind"] == "texto"
    assert result["action"] == "solicitar_classificacao"


def test_processes_image_message() -> None:
    result = process_received_message(
        ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.IMAGE,
            raw_type="imageMessage",
        )
    )

    assert result["message_kind"] == "imagem"
    assert result["action"] == "solicitar_classificacao"


def test_processes_audio_message() -> None:
    result = process_received_message(
        ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.AUDIO,
            raw_type="audioMessage",
        )
    )

    assert result["message_kind"] == "audio"
    assert result["action"] == "solicitar_classificacao"


def test_processes_video_message() -> None:
    result = process_received_message(
        ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.VIDEO,
            raw_type="videoMessage",
        )
    )

    assert result["message_kind"] == "video"
    assert result["action"] == "solicitar_classificacao"


def test_processes_document_message() -> None:
    result = process_received_message(
        ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.DOCUMENT,
            raw_type="documentMessage",
        )
    )

    assert result["message_kind"] == "documento"
    assert result["action"] == "solicitar_classificacao"


def test_processes_unknown_message_without_classification_action() -> None:
    result = process_received_message(
        ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.UNKNOWN,
            raw_type="stickerMessage",
        )
    )

    assert result["processed"] is True
    assert result["message_kind"] == "desconhecida"
    assert result["action"] == "ignorar"


def test_processes_ignored_mapping_result() -> None:
    result = process_mapping_result(
        EvolutionMessageMappingResult(
            message=None,
            ignored_reason="evento_ignorado",
            event="connection.update",
        )
    )

    assert result == {
        "processed": False,
        "reason": "evento_ignorado",
        "event": "connection.update",
    }


def test_identifies_command_message() -> None:
    message = ReceivedMessage(
        message_id="MSG1",
        sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
        message_type=MessageType.TEXT,
        raw_type="conversation",
        text="!ajuda",
    )

    assert is_command_message(message) is True


def test_does_not_identify_regular_text_as_command() -> None:
    message = ReceivedMessage(
        message_id="MSG1",
        sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
        message_type=MessageType.TEXT,
        raw_type="conversation",
        text="Boa noite, tudo bem?",
    )

    assert is_command_message(message) is False


def test_bare_command_words_are_recognized_without_bang() -> None:
    for word in ("cancelar", "Status", "recomeçar", "AJUDA"):
        message = ReceivedMessage(
            message_id="MSG1",
            sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
            message_type=MessageType.TEXT,
            raw_type="conversation",
            text=word,
        )
        assert is_command_message(message) is True

from app.models.message import Media, MessageType, ReceivedMessage, Sender


def test_received_message_model_represents_text_message() -> None:
    sender = Sender(remote_jid="556299999999@s.whatsapp.net")
    message = ReceivedMessage(
        message_id="MSG1",
        sender=sender,
        message_type=MessageType.TEXT,
        raw_type="conversation",
        text="Ola",
    )

    assert message.message_id == "MSG1"
    assert message.sender == sender
    assert message.message_type is MessageType.TEXT
    assert message.text == "Ola"
    assert message.media is None


def test_media_model_represents_optional_media_metadata() -> None:
    media = Media(
        mimetype="application/pdf",
        file_name="arquivo.pdf",
        caption="Documento",
        metadata={"mimetype": "application/pdf"},
    )

    assert media.mimetype == "application/pdf"
    assert media.file_name == "arquivo.pdf"
    assert media.caption == "Documento"
    assert media.metadata == {"mimetype": "application/pdf"}

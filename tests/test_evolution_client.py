import asyncio

import httpx
import pytest

from app.models.message import Media, MessageType, ReceivedMessage, Sender
from app.services.evolution_client import (
    EvolutionClient,
    EvolutionConnectionError,
    EvolutionHttpError,
    EvolutionInvalidResponseError,
)


def _media_message() -> ReceivedMessage:
    return ReceivedMessage(
        message_id="MSG1",
        sender=Sender(remote_jid="556299999999@s.whatsapp.net"),
        message_type=MessageType.AUDIO,
        raw_type="audioMessage",
        media=Media(mimetype="audio/ogg", file_name="audio.ogg"),
    )


def test_health_returns_json_payload() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code=200,
            json={"status": "ok"},
            request=request,
        )
    )
    client = EvolutionClient(
        base_url="http://evolution.test",
        api_key="test-key",
        timeout_seconds=1.0,
        transport=transport,
    )

    result = asyncio.run(client.health())

    assert result == {"status": "ok"}


def test_health_sends_api_key_header() -> None:
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers["apikey"] = request.headers["apikey"]
        return httpx.Response(status_code=200, json={"status": "ok"}, request=request)

    client = EvolutionClient(
        base_url="http://evolution.test",
        api_key="test-key",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    asyncio.run(client.health())

    assert captured_headers["apikey"] == "test-key"


def test_client_uses_configurable_timeout() -> None:
    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=2.5,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status_code=200, json={}, request=request)
        ),
    )

    assert client.timeout_seconds == 2.5


def test_download_media_returns_decoded_media() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url_path"] = request.url.path
        captured_request["json"] = request.read().decode()
        return httpx.Response(
            status_code=200,
            json={
                "base64": "YXVkaW8=",
                "mimetype": "audio/ogg",
                "fileName": "audio.ogg",
            },
            request=request,
        )

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(client.download_media(_media_message()))

    assert captured_request["method"] == "POST"
    assert captured_request["url_path"] == "/chat/getBase64FromMediaMessage/ykmedia"
    assert result.message_id == "MSG1"
    assert result.content == b"audio"
    assert result.mimetype == "audio/ogg"
    assert result.size_bytes == 5
    assert result.file_name == "audio.ogg"


def test_download_media_raises_invalid_response_when_base64_is_missing() -> None:
    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status_code=200, json={"mimetype": "audio/ogg"}, request=request)
        ),
    )

    with pytest.raises(EvolutionInvalidResponseError):
        asyncio.run(client.download_media(_media_message()))


def test_download_media_raises_invalid_response_when_base64_is_invalid() -> None:
    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                status_code=200,
                json={"base64": "not valid base64"},
                request=request,
            )
        ),
    )

    with pytest.raises(EvolutionInvalidResponseError):
        asyncio.run(client.download_media(_media_message()))


def test_health_raises_standardized_http_error() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code=500,
            json={"message": "error"},
            request=request,
        )
    )
    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=transport,
    )

    with pytest.raises(EvolutionHttpError) as exc_info:
        asyncio.run(client.health())

    assert exc_info.value.status_code == 500


def test_health_raises_standardized_connection_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection failed", request=request)

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(EvolutionConnectionError):
        asyncio.run(client.health())


def test_health_raises_standardized_invalid_json_error() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code=200,
            content=b"not-json",
            request=request,
        )
    )
    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=transport,
    )

    with pytest.raises(EvolutionInvalidResponseError):
        asyncio.run(client.health())


def test_health_raises_standardized_unsupported_json_error() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            status_code=200,
            json=["unexpected"],
            request=request,
        )
    )
    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=transport,
    )

    with pytest.raises(EvolutionInvalidResponseError):
        asyncio.run(client.health())

import asyncio

import httpx
import pytest

from app.models.interactive import InteractiveOption
from app.models.message import Media, MessageType, ReceivedMessage, Sender
from app.core.config import settings
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


def test_client_uses_current_runtime_api_key_when_no_explicit_key_is_supplied(monkeypatch) -> None:
    captured_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_headers["apikey"] = request.headers["apikey"]
        return httpx.Response(status_code=200, json={"status": "ok"}, request=request)

    monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "initial-key")
    client = EvolutionClient(base_url="http://evolution.test", transport=httpx.MockTransport(handler))
    monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "prepared-key")

    asyncio.run(client.health())

    assert captured_headers["apikey"] == "prepared-key"


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


def test_send_text_message_uses_official_endpoint_and_payload() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url_path"] = request.url.path
        captured_request["json"] = request.read().decode()
        return httpx.Response(
            status_code=200,
            json={"status": "PENDING"},
            request=request,
        )

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        client.send_text_message(
            recipient="556299999999@s.whatsapp.net",
            text="Recebi seu arquivo.",
        )
    )

    assert captured_request["method"] == "POST"
    assert captured_request["url_path"] == "/message/sendText/ykmedia"
    assert captured_request["json"] == (
        '{"number":"556299999999","text":"Recebi seu arquivo."}'
    )
    assert result == {"status": "PENDING"}


def test_send_text_message_rejects_empty_text() -> None:
    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(
            lambda request: httpx.Response(status_code=200, json={}, request=request)
        ),
    )

    with pytest.raises(EvolutionInvalidResponseError):
        asyncio.run(client.send_text_message("556299999999@s.whatsapp.net", " "))


def test_send_reply_buttons_uses_official_endpoint_and_payload() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url_path"] = request.url.path
        captured_request["json"] = request.content.decode("utf-8")
        return httpx.Response(status_code=201, json={"status": "PENDING"}, request=request)

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        client.send_reply_buttons(
            recipient="556299999999@s.whatsapp.net",
            text="Escolha",
            options=[InteractiveOption(id="filename:keep_original", title="Manter nome")],
            footer="YkMedia",
        )
    )

    assert captured_request["method"] == "POST"
    assert captured_request["url_path"] == "/message/sendButtons/ykmedia"
    assert '"number":"556299999999"' in str(captured_request["json"])
    assert '"type":"reply"' in str(captured_request["json"])
    assert '"displayText":"Manter nome"' in str(captured_request["json"])
    assert '"id":"filename:keep_original"' in str(captured_request["json"])
    assert result == {"status": "PENDING"}


def test_send_selection_list_uses_official_endpoint_and_payload() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url_path"] = request.url.path
        captured_request["json"] = request.content.decode("utf-8")
        return httpx.Response(status_code=201, json={"status": "PENDING"}, request=request)

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        client.send_selection_list(
            recipient="556299999999@s.whatsapp.net",
            text="Categorias",
            button_text="Ver categorias",
            options=[InteractiveOption(id="category:1", title="Louvores")],
            footer="YkMedia",
        )
    )

    assert captured_request["method"] == "POST"
    assert captured_request["url_path"] == "/message/sendList/ykmedia"
    assert '"buttonText":"Ver categorias"' in str(captured_request["json"])
    assert '"rowId":"category:1"' in str(captured_request["json"])
    assert '"description"' not in str(captured_request["json"])
    assert result == {"status": "PENDING"}


def test_connect_instance_uses_official_endpoint() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url_path"] = request.url.path
        return httpx.Response(
            status_code=200,
            json={"qrcode": {"base64": "data:image/png;base64,abc"}},
            request=request,
        )

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(client.connect_instance())

    assert captured_request["method"] == "GET"
    assert captured_request["url_path"] == "/instance/connect/ykmedia"
    assert result == {"qrcode": {"base64": "data:image/png;base64,abc"}}


def test_create_instance_uses_official_endpoint() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url_path"] = request.url.path
        captured_request["json"] = request.content.decode("utf-8")
        return httpx.Response(status_code=201, json={"instance": {"instanceName": "ykmedia"}}, request=request)

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(client.create_instance())

    assert captured_request["method"] == "POST"
    assert captured_request["url_path"] == "/instance/create"
    assert '"instanceName":"ykmedia"' in str(captured_request["json"])
    assert '"integration":"WHATSAPP-BAILEYS"' in str(captured_request["json"])
    assert result == {"instance": {"instanceName": "ykmedia"}}


def test_set_webhook_uses_official_endpoint() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url_path"] = request.url.path
        captured_request["json"] = request.content.decode("utf-8")
        return httpx.Response(status_code=200, json={"webhook": {"enabled": True}}, request=request)

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(client.set_webhook("http://host.docker.internal:8010/webhooks/evolution", "secret"))

    assert captured_request["method"] == "POST"
    assert captured_request["url_path"] == "/webhook/set/ykmedia"
    assert '"webhook":{' in str(captured_request["json"])
    assert '"byEvents":false' in str(captured_request["json"])
    assert '"base64":false' in str(captured_request["json"])
    assert '"x-webhook-secret":"secret"' in str(captured_request["json"])
    assert result == {"webhook": {"enabled": True}}


def test_fetch_profile_picture_url_uses_official_endpoint() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url_path"] = request.url.path
        captured_request["json"] = request.content.decode("utf-8")
        return httpx.Response(
            status_code=200,
            json={"profilePictureUrl": "https://example.com/photo.jpg"},
            request=request,
        )

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(client.fetch_profile_picture_url("556299999999@s.whatsapp.net"))

    assert captured_request["method"] == "POST"
    assert captured_request["url_path"] == "/chat/fetchProfilePictureUrl/ykmedia"
    assert '"number":"556299999999"' in str(captured_request["json"])
    assert result == {"profilePictureUrl": "https://example.com/photo.jpg"}


def test_get_connection_state_uses_official_endpoint() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url_path"] = request.url.path
        return httpx.Response(
            status_code=200,
            json={"instance": {"state": "open"}},
            request=request,
        )

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(client.get_connection_state())

    assert captured_request["method"] == "GET"
    assert captured_request["url_path"] == "/instance/connectionState/ykmedia"
    assert result == {"instance": {"state": "open"}}


def test_logout_instance_uses_official_endpoint() -> None:
    captured_request: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["method"] = request.method
        captured_request["url_path"] = request.url.path
        return httpx.Response(status_code=200, json={"status": "SUCCESS"}, request=request)

    client = EvolutionClient(
        base_url="http://evolution.test",
        timeout_seconds=1.0,
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(client.logout_instance())

    assert captured_request["method"] == "DELETE"
    assert captured_request["url_path"] == "/instance/logout/ykmedia"
    assert result == {"status": "SUCCESS"}


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

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_receives_message_upsert() -> None:
    payload = {
        "event": "messages.upsert",
        "instance": "ykmedia",
        "data": {
            "key": {
                "id": "ABC123",
                "remoteJid": "556299999999@s.whatsapp.net",
                "fromMe": False,
            },
            "message": {
                "audioMessage": {
                    "mimetype": "audio/ogg; codecs=opus"
                }
            },
        },
    }

    response = client.post("/webhooks/evolution", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["received"] is True
    assert body["processed"] is True
    assert body["message_type"] == "audioMessage"


def test_ignores_own_message() -> None:
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {
                "id": "OWN1",
                "remoteJid": "556299999999@s.whatsapp.net",
                "fromMe": True,
            },
            "message": {"conversation": "teste"},
        },
    }

    response = client.post("/webhooks/evolution", json=payload)
    assert response.status_code == 200
    assert response.json()["reason"] == "mensagem_propria"

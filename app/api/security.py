"""Autenticacao das rotas de API voltadas ao aplicativo desktop.

O backend roda como sidecar local, mas precisa aceitar conexoes em todas as
interfaces para que o container Docker da Evolution alcance o webhook. Para que
essa exposicao na rede local nao entregue conversas, arquivos e configuracoes a
terceiros, cada rota do aplicativo exige um token compartilhado apenas com a
interface Tauri. O webhook usa o seu proprio segredo (WEBHOOK_SECRET).
"""

import hmac

from fastapi import Header, HTTPException, status

from app.core.config import settings

_BEARER_PREFIX = "bearer "


def require_api_token(authorization: str | None = Header(default=None)) -> None:
    expected = settings.API_AUTH_TOKEN
    if not expected:
        return

    provided = ""
    if authorization and authorization[: len(_BEARER_PREFIX)].lower() == _BEARER_PREFIX:
        provided = authorization[len(_BEARER_PREFIX) :].strip()

    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de API invalido.",
        )

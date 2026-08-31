"""Ativacao da licenca gratuita exigida pela Evolution API a partir da 2.4.0.

Sem ativar, todos os endpoints respondem HTTP 503 (`LICENSE_REQUIRED`) e o
YkMedia nao consegue nem criar a instancia do WhatsApp.

O fluxo tem tres passos:

1. `GET /license/register?redirect_uri=...` devolve uma URL do servidor de
   licencas com um token de uso unico;
2. a pessoa se autentica nessa URL (magic link, Google ou GitHub);
3. o navegador volta para `redirect_uri` com `?code=...`, e
   `GET /license/activate?code=...` troca o codigo pela chave definitiva.

O `redirect_uri` e o que fecha o ciclo sozinho: sem ele o codigo fica preso no
navegador e a instancia nunca ativa.

A ativacao automatica por `EVOLUTION_OPERATOR_EMAIL` documentada pela Evolution
nao funciona na 2.4.0-rc2: o runtime so tenta esse caminho quando a chave global
e vazia, mas `env.config` aplica um default embutido, entao a condicao nunca e
satisfeita.
"""

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LicenseStatus(StrEnum):
    ACTIVE = "ATIVA"
    PENDING = "PENDENTE"
    NOT_REQUIRED = "NAO_EXIGIDA"
    UNAVAILABLE = "INDISPONIVEL"


@dataclass(frozen=True, slots=True)
class LicenseState:
    status: LicenseStatus
    register_url: str | None = None
    message: str = ""


class EvolutionLicenseService:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        self._explicit_base_url = base_url.rstrip("/") if base_url else None
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    @property
    def base_url(self) -> str:
        """Lida a cada uso: o preparo pode trocar a porta com o app rodando."""
        if self._explicit_base_url is not None:
            return self._explicit_base_url
        return settings.EVOLUTION_BASE_URL.rstrip("/")

    @property
    def _headers(self) -> dict[str, str]:
        return {"apikey": self._api_key if self._api_key is not None else settings.EVOLUTION_API_KEY}

    def status(self) -> LicenseState:
        payload = self._get("/license/status")
        if payload is None:
            return LicenseState(
                status=LicenseStatus.UNAVAILABLE,
                message=(
                    "Nao foi possivel falar com a Evolution. Verifique se o Docker "
                    "Desktop esta aberto e use Preparar sistema para subir os servicos."
                ),
            )

        if self._endpoint_missing(payload):
            return LicenseState(
                status=LicenseStatus.NOT_REQUIRED,
                message="Esta versao da Evolution nao exige licenca.",
            )

        if str(payload.get("status", "")).lower() == "active":
            return LicenseState(status=LicenseStatus.ACTIVE, message="Licenca ativa.")

        return LicenseState(status=LicenseStatus.PENDING, message="Licenca ainda nao ativada.")

    @staticmethod
    def _endpoint_missing(payload: dict[str, Any]) -> bool:
        """Versoes anteriores a 2.4.0 nao tem as rotas de licenca."""
        return payload.get("status") == 404

    def start_registration(self, redirect_uri: str | None = None) -> LicenseState:
        """Devolve a URL onde a pessoa conclui o cadastro."""
        target = redirect_uri or self._default_redirect_uri()
        payload = self._get(f"/license/register?redirect_uri={quote(target, safe='')}")
        if payload is None:
            return LicenseState(
                status=LicenseStatus.UNAVAILABLE,
                message=(
                    "Nao foi possivel falar com a Evolution. Verifique se o Docker "
                    "Desktop esta aberto e use Preparar sistema para subir os servicos."
                ),
            )

        if self._endpoint_missing(payload):
            return LicenseState(
                status=LicenseStatus.NOT_REQUIRED,
                message="Esta versao da Evolution nao exige licenca.",
            )

        if str(payload.get("status", "")).lower() == "active":
            return LicenseState(status=LicenseStatus.ACTIVE, message="Licenca ja estava ativa.")

        url = str(payload.get("register_url") or "")
        if not url:
            return LicenseState(
                status=LicenseStatus.UNAVAILABLE,
                message="A Evolution nao devolveu o endereco de cadastro.",
            )

        return LicenseState(
            status=LicenseStatus.PENDING,
            register_url=url,
            message="Abra o endereco para concluir o cadastro gratuito.",
        )

    def activate(self, code: str) -> LicenseState:
        payload = self._get(f"/license/activate?code={quote(code, safe='')}")
        if payload is None:
            return LicenseState(
                status=LicenseStatus.UNAVAILABLE,
                message=(
                    "Nao foi possivel falar com a Evolution. Verifique se o Docker "
                    "Desktop esta aberto e use Preparar sistema para subir os servicos."
                ),
            )

        if str(payload.get("status", "")).lower() == "active":
            logger.info("Licenca da Evolution ativada.")
            return LicenseState(status=LicenseStatus.ACTIVE, message="Licenca ativada.")

        return LicenseState(
            status=LicenseStatus.PENDING,
            message=str(payload.get("details") or payload.get("error") or "Codigo invalido ou expirado."),
        )

    def _default_redirect_uri(self) -> str:
        return f"{self.base_url}/license/activate"

    def _get(self, path: str) -> dict[str, Any] | None:
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                headers=self._headers,
                timeout=self._timeout_seconds,
            )
        except httpx.RequestError as exc:
            logger.warning("Falha ao consultar a licenca da Evolution: %s", exc)
            return None

        try:
            payload = response.json()
        except ValueError:
            return None

        return payload if isinstance(payload, dict) else None

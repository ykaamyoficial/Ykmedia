"""Reconhece o tipo de falha do Docker para responder com a acao certa.

Ate a 0.4.1 qualquer erro recebia o mesmo conselho ("clique novamente, o
download continua de onde parou"). Num conflito de porta isso e falso: repetir
nunca resolve, e o usuario fica preso repetindo uma acao inutil.
"""

import re
import subprocess
from dataclasses import dataclass
from enum import StrEnum

#: O Compose escreve o andamento (Running / Waiting / Healthy / Starting) na
#: saida de erro. Sao linhas de rotina normal, nao falhas.
_PROGRESS_LINE = re.compile(
    r"^\s*(Container|Network|Volume|Image)\s+\S+\s+"
    r"(Running|Waiting|Healthy|Starting|Started|Created|Creating|Pulling|Pulled|Exists)\s*$"
)
_PORT_PATTERN = re.compile(r"0\.0\.0\.0:(\d+)|listen tcp[^:]*:(\d+)")


class DockerFailureKind(StrEnum):
    PORT_RESERVED = "PORTA_RESERVADA"
    PORT_IN_USE = "PORTA_OCUPADA"
    NO_DISK = "SEM_ESPACO"
    NO_NETWORK = "SEM_REDE"
    DAEMON_DOWN = "DOCKER_PARADO"
    TIMEOUT = "TEMPO_ESGOTADO"
    UNKNOWN = "DESCONHECIDO"


@dataclass(frozen=True, slots=True)
class DockerFailure:
    kind: DockerFailureKind
    headline: str
    action: str
    detail: str
    #: Se o proprio sistema consegue contornar sem pedir nada ao usuario.
    can_retry_automatically: bool = False
    port: int | None = None


def classify(error: str | BaseException) -> DockerFailure:
    if isinstance(error, subprocess.TimeoutExpired):
        return DockerFailure(
            kind=DockerFailureKind.TIMEOUT,
            headline="O download dos componentes demorou demais e foi interrompido.",
            action=(
                "Verifique a internet e clique em Preparar sistema novamente: "
                "o Docker retoma de onde parou."
            ),
            detail=str(error),
        )

    raw = _raw_text(error)
    signal = _signal_lines(raw)
    lowered = signal.lower()

    if "permission" in lowered or "permiss" in lowered or "acesso" in lowered:
        if "bind" in lowered or "ports are not available" in lowered:
            port = _extract_port(signal)
            return DockerFailure(
                kind=DockerFailureKind.PORT_RESERVED,
                headline=(
                    f"A porta {port} esta bloqueada pelo Windows."
                    if port
                    else "A porta usada pela Evolution esta bloqueada pelo Windows."
                ),
                action=(
                    "O Windows reserva faixas de portas para uso interno e essa faixa "
                    "mudou. Vou escolher outra porta automaticamente."
                ),
                detail=raw,
                can_retry_automatically=True,
                port=port,
            )

    if "address already in use" in lowered or "port is already allocated" in lowered:
        port = _extract_port(signal)
        return DockerFailure(
            kind=DockerFailureKind.PORT_IN_USE,
            headline=(
                f"A porta {port} ja esta sendo usada por outro programa."
                if port
                else "A porta da Evolution ja esta sendo usada por outro programa."
            ),
            action="Vou escolher outra porta automaticamente.",
            detail=raw,
            can_retry_automatically=True,
            port=port,
        )

    if "no space left on device" in lowered:
        return DockerFailure(
            kind=DockerFailureKind.NO_DISK,
            headline="O disco ficou sem espaco durante a instalacao.",
            action=(
                "Libere espaco no disco C: (os componentes ocupam cerca de 2 GB) "
                "e clique em Preparar sistema novamente."
            ),
            detail=raw,
        )

    if any(
        marker in lowered
        for marker in ("dial tcp", "tls handshake", "no such host", "connection refused while", "i/o timeout")
    ):
        return DockerFailure(
            kind=DockerFailureKind.NO_NETWORK,
            headline="Nao foi possivel baixar os componentes.",
            action=(
                "Verifique a conexao com a internet e clique em Preparar sistema "
                "novamente: o download retoma de onde parou."
            ),
            detail=raw,
        )

    if "cannot connect to the docker daemon" in lowered or "daemon is not running" in lowered:
        return DockerFailure(
            kind=DockerFailureKind.DAEMON_DOWN,
            headline="O Docker Desktop nao esta em execucao.",
            action=(
                "Abra o Docker Desktop e espere o icone da baleia ficar verde. "
                "Depois clique em Preparar sistema novamente."
            ),
            detail=raw,
        )

    return DockerFailure(
        kind=DockerFailureKind.UNKNOWN,
        headline=signal.splitlines()[0] if signal else "O Docker recusou o comando.",
        action=(
            "Clique em Copiar detalhes e envie a mensagem para o suporte: "
            "esta falha ainda nao e conhecida."
        ),
        detail=raw,
    )


def _raw_text(error: str | BaseException) -> str:
    if isinstance(error, subprocess.CalledProcessError):
        parts = [str(error.stderr or "").strip(), str(error.stdout or "").strip()]
        joined = "\n".join(part for part in parts if part)
        return joined or str(error)
    return str(error).strip()


def _signal_lines(raw: str) -> str:
    """Descarta o andamento do Compose e devolve so o que descreve a falha."""
    lines = [line for line in raw.splitlines() if line.strip() and not _PROGRESS_LINE.match(line)]
    return "\n".join(lines).strip()


def _extract_port(text: str) -> int | None:
    match = _PORT_PATTERN.search(text)
    if not match:
        return None
    value = match.group(1) or match.group(2)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

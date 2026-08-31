"""O conselho na tela precisa corresponder a falha.

A versao 0.4.1 dizia "clique novamente, o download continua de onde parou" para
qualquer erro -- inclusive um conflito de porta, onde repetir nunca funciona.
"""

import subprocess

from app.services.docker_failure import DockerFailureKind, classify

# Texto exato da maquina do usuario em 30/08/2026.
PORT_RESERVED_OUTPUT = (
    "Container ykmedia_redis Running\n"
    "Container ykmedia_postgres Healthy\n"
    "Container ykmedia_evolution Starting\n"
    "Error response from daemon: ports are not available: exposing port "
    "TCP 0.0.0.0:8080 -> 127.0.0.1:0: listen tcp 0.0.0.0:8080: bind: Foi feita "
    "uma tentativa de acesso a um soquete de uma maneira que e proibida pelas "
    "permissoes de acesso."
)


def test_reserved_port_is_recognised_and_is_auto_recoverable() -> None:
    failure = classify(PORT_RESERVED_OUTPUT)

    assert failure.kind is DockerFailureKind.PORT_RESERVED
    assert failure.can_retry_automatically is True
    assert "8080" in failure.headline
    # O conselho errado da 0.4.1 nao pode reaparecer aqui.
    assert "download" not in failure.action.lower()


def test_progress_noise_is_dropped_from_the_headline() -> None:
    """O Compose escreve o andamento no stderr; sete linhas de rotina normal
    empurravam a unica linha util para o meio do bloco."""
    failure = classify(PORT_RESERVED_OUTPUT)

    assert "Running" not in failure.headline
    assert "Starting" not in failure.headline
    # O log completo continua disponivel para o suporte.
    assert "ykmedia_redis Running" in failure.detail


def test_busy_port_is_separated_from_reserved_port() -> None:
    failure = classify("Error response from daemon: address already in use")

    assert failure.kind is DockerFailureKind.PORT_IN_USE
    assert failure.can_retry_automatically is True


def test_network_failure_is_the_one_case_where_retrying_helps() -> None:
    failure = classify("failed to resolve reference: dial tcp: lookup registry-1.docker.io")

    assert failure.kind is DockerFailureKind.NO_NETWORK
    assert "internet" in failure.action.lower()
    assert failure.can_retry_automatically is False


def test_disk_full_says_what_is_wrong() -> None:
    failure = classify("write /var/lib/docker: no space left on device")

    assert failure.kind is DockerFailureKind.NO_DISK
    assert "espaco" in failure.action.lower()


def test_daemon_down_points_at_docker_desktop() -> None:
    failure = classify("Cannot connect to the Docker daemon at npipe:////./pipe/docker_engine.")

    assert failure.kind is DockerFailureKind.DAEMON_DOWN
    assert "Docker Desktop" in failure.action


def test_timeout_keeps_the_resumable_download_message() -> None:
    failure = classify(subprocess.TimeoutExpired(cmd=["docker", "compose", "pull"], timeout=3600))

    assert failure.kind is DockerFailureKind.TIMEOUT
    assert "retoma de onde parou" in failure.action


def test_unknown_failure_does_not_invent_advice() -> None:
    """Chutar um conselho e pior que admitir que nao sabemos: manda o usuario
    repetir acoes inuteis."""
    failure = classify("Error response from daemon: something nobody has seen before")

    assert failure.kind is DockerFailureKind.UNKNOWN
    assert "suporte" in failure.action.lower()
    assert failure.can_retry_automatically is False

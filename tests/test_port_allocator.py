"""A porta 8080 fixa era o unico caminho: quando o Windows a reservava, a
instalacao inteira morria sem alternativa. Estes testes cobrem a escolha
automatica de uma porta utilizavel."""

import subprocess

from app.services.port_allocator import PortAllocator

# Saida real do `netsh interface ipv4 show excludedportrange protocol=tcp`
# numa maquina com Hyper-V ativo: o Windows reserva blocos inteiros, e o bloco
# 8058-8157 engole a 8080.
NETSH_OUTPUT = """
Intervalo de porta de protocolo tcp
--------------------------------

Porta inicial    Porta final
-------------    -----------
      1024          1123
      8058          8085
     50000         50059

* - Porta administrada
"""


def _runner(stdout: str = NETSH_OUTPUT, returncode: int = 0):
    def run(command, **kwargs):
        return subprocess.CompletedProcess(args=command, returncode=returncode, stdout=stdout, stderr="")

    return run


def test_reserved_windows_range_is_detected() -> None:
    allocator = PortAllocator(is_windows=True, command_runner=_runner())

    assert allocator.is_reserved(8080) is True
    assert allocator.is_reserved(8090) is False
    assert allocator.is_reserved(1050) is True


def test_preferred_port_is_kept_when_it_works() -> None:
    """Quem ja funciona nao pode ter a porta trocada: o pareamento do WhatsApp
    e a URL da Evolution dependem dela."""
    allocator = PortAllocator(is_windows=True, command_runner=_runner(stdout=""), binder=lambda port: True)

    assert allocator.allocate(preferred=8080) == 8080


def test_falls_back_when_the_preferred_port_is_reserved() -> None:
    allocator = PortAllocator(is_windows=True, command_runner=_runner(), binder=lambda port: True)

    port = allocator.allocate(preferred=8080)

    assert port != 8080
    assert allocator.is_reserved(port) is False


def test_a_port_that_fails_to_bind_is_skipped() -> None:
    """A lista do Windows nao cobre tudo: outro processo pode estar ouvindo."""
    busy = {8080, 8090}
    allocator = PortAllocator(
        command_runner=_runner(stdout=""),
        binder=lambda port: port not in busy,
    )

    port = allocator.allocate(preferred=8080)

    assert port not in busy


def test_missing_netsh_does_not_break_the_allocation() -> None:
    """Em maquinas sem netsh (ou fora do Windows) o teste de bind basta."""

    def failing_runner(command, **kwargs):
        raise FileNotFoundError("netsh")

    allocator = PortAllocator(is_windows=True, command_runner=failing_runner, binder=lambda port: True)

    assert allocator.allocate(preferred=8080) == 8080

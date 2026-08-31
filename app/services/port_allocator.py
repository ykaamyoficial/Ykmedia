"""Escolhe uma porta TCP que o Windows realmente permita publicar.

Com Hyper-V ou WSL2 ativos -- e o Docker Desktop exige um dos dois -- o servico
WinNAT reserva blocos inteiros de portas ao iniciar, e esses blocos mudam a cada
reinicio da maquina. Quando um bloco cai sobre a 8080, o Docker falha com
"bind: ... proibida pelas permissoes de acesso" e nenhuma tentativa de repetir
resolve. Fixar a porta no compose deixava a instalacao sem saida.
"""

import os
import re
import socket
import subprocess
from pathlib import Path

_RANGE_LINE = re.compile(r"^\s*(\d+)\s+(\d+)\s*$")


class PortAllocator:
    #: A 8080 vem primeiro de proposito: quem ja tem o ambiente funcionando nao
    #: pode ter a porta trocada, porque a URL da Evolution e o pareamento do
    #: WhatsApp dependem dela.
    CANDIDATES = (8080, 8090, 8081, 18080, 28080, 38080)

    def __init__(
        self,
        command_runner=subprocess.run,
        binder=None,
        #: Injetavel para que o comportamento no Windows possa ser testado na
        #: integracao continua, que roda em Linux.
        is_windows: bool | None = None,
    ) -> None:
        self.command_runner = command_runner
        self._binder = binder or self._can_bind
        self._is_windows = os.name == "nt" if is_windows is None else is_windows
        self._reserved_ranges: list[tuple[int, int]] | None = None

    def allocate(self, preferred: int | None = None) -> int:
        candidates = list(self.CANDIDATES)
        if preferred is not None and preferred in candidates:
            candidates.remove(preferred)
        if preferred is not None:
            candidates.insert(0, preferred)

        for port in candidates:
            if self.is_available(port):
                return port

        # Nenhuma das conhecidas serve: pede uma efemera ao proprio sistema, que
        # por definicao nao esta reservada.
        return self._ephemeral_port()

    def is_available(self, port: int) -> bool:
        return not self.is_reserved(port) and self._binder(port)

    def is_reserved(self, port: int) -> bool:
        return any(start <= port <= end for start, end in self._excluded_ranges())

    def _excluded_ranges(self) -> list[tuple[int, int]]:
        if self._reserved_ranges is None:
            self._reserved_ranges = self._read_excluded_ranges()
        return self._reserved_ranges

    def _read_excluded_ranges(self) -> list[tuple[int, int]]:
        if not self._is_windows:
            return []

        try:
            result = self.command_runner(
                [
                    "netsh",
                    "interface",
                    "ipv4",
                    "show",
                    "excludedportrange",
                    "protocol=tcp",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=20,
                **self._no_window(),
            )
        except (OSError, subprocess.SubprocessError):
            # Sem a lista o teste de bind ainda protege: nao vale falhar aqui.
            return []

        return self._parse_ranges(str(getattr(result, "stdout", "") or ""))

    def _parse_ranges(self, output: str) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []
        for line in output.splitlines():
            match = _RANGE_LINE.match(line)
            if not match:
                continue
            start, end = int(match.group(1)), int(match.group(2))
            if start <= end:
                ranges.append((start, end))
        return ranges

    def _can_bind(self, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False

    def _ephemeral_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(("0.0.0.0", 0))
            return int(probe.getsockname()[1])

    def _no_window(self) -> dict[str, object]:
        if os.name == "nt":
            return {"creationflags": subprocess.CREATE_NO_WINDOW}
        return {}


def read_port_from_env(env_path: Path, key: str = "EVOLUTION_PORT") -> int | None:
    """Le a porta ja escolhida numa execucao anterior, se houver."""
    if not env_path.exists():
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name.strip() == key:
            try:
                return int(value.strip())
            except ValueError:
                return None
    return None

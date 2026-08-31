import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.core.config import settings
from app.services.docker_failure import classify
from app.services.port_allocator import PortAllocator, read_port_from_env

logger = logging.getLogger(__name__)

#: A Evolution escreve o log colorido; os codigos ANSI viram lixo ilegivel na
#: tela ("[1m[37m[Evolution API]").
_ANSI = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


class EnvironmentStatus(StrEnum):
    READY = "PRONTO"
    DOCKER_MISSING = "DOCKER_NAO_INSTALADO"
    DOCKER_STOPPED = "DOCKER_PARADO"
    CONFIG_MISSING = "CONFIGURACAO_PENDENTE"
    ERROR = "ERRO"


@dataclass(frozen=True, slots=True)
class ContainerState:
    name: str
    service: str
    state: str
    health: str
    exit_code: int

    @property
    def is_up(self) -> bool:
        """"running" com health "starting" ainda conta: o container esta de pe."""
        return self.state.lower() == "running" and self.health.lower() != "unhealthy"


@dataclass(frozen=True, slots=True)
class EnvironmentCheck:
    status: EnvironmentStatus
    docker_installed: bool
    docker_running: bool
    compose_available: bool
    containers_running: bool
    #: Manchete em linguagem comum. O log tecnico vai em `detail`, para que a
    #: tela nao precise misturar os dois no mesmo paragrafo.
    message: str
    detail: str = ""
    action: str = ""
    port: int | None = None


class EnvironmentManager:
    _CONTAINER_NAMES = {"ykmedia_evolution", "ykmedia_postgres", "ykmedia_redis"}

    def __init__(
        self,
        runtime_root: str | Path | None = None,
        command_runner=subprocess.run,
        port_allocator=None,
    ) -> None:
        self.runtime_root = Path(
            runtime_root or Path(os.environ.get("LOCALAPPDATA", ".")) / "YkMedia"
        ).resolve()
        self.command_runner = command_runner
        self.port_allocator = port_allocator or PortAllocator(command_runner=command_runner)

    def check(self) -> EnvironmentCheck:
        docker_installed = self._command_exists("docker")
        compose_available = self._source_compose_path().exists()

        if not docker_installed:
            return EnvironmentCheck(
                status=EnvironmentStatus.DOCKER_MISSING,
                docker_installed=False,
                docker_running=False,
                compose_available=compose_available,
                containers_running=False,
                message="Docker Desktop nao esta instalado.",
            )

        docker_running = self._docker_is_running()
        if not docker_running:
            return EnvironmentCheck(
                status=EnvironmentStatus.DOCKER_STOPPED,
                docker_installed=True,
                docker_running=False,
                compose_available=compose_available,
                containers_running=False,
                message="Docker esta instalado, mas nao esta em execucao.",
            )

        containers_running = self._containers_are_running()
        return EnvironmentCheck(
            status=EnvironmentStatus.READY if containers_running else EnvironmentStatus.CONFIG_MISSING,
            docker_installed=True,
            docker_running=True,
            compose_available=compose_available,
            containers_running=containers_running,
            message="Ambiente pronto." if containers_running else "Containers ainda nao foram iniciados.",
        )

    def prepare(self, install_docker: bool = True) -> EnvironmentCheck:
        if not self._command_exists("docker"):
            if install_docker:
                self._install_docker_desktop()
            if not self._command_exists("docker"):
                return EnvironmentCheck(
                    status=EnvironmentStatus.DOCKER_MISSING,
                    docker_installed=False,
                    docker_running=False,
                    compose_available=self._source_compose_path().exists(),
                    containers_running=False,
                    message=(
                        "Docker Desktop nao foi encontrado. A instalacao pode exigir "
                        "permissao de administrador e reinicio do Windows."
                    ),
                )

        if not self._docker_is_running():
            self._start_docker_desktop()
            # O Docker Desktop leva de 2 a 4 minutos num arranque frio; 90s
            # desistia antes da hora e o preparo parava no primeiro passo.
            self._wait_for_docker(timeout_seconds=240)

        if not self._docker_is_running():
            return EnvironmentCheck(
                status=EnvironmentStatus.DOCKER_STOPPED,
                docker_installed=True,
                docker_running=False,
                compose_available=self._source_compose_path().exists(),
                containers_running=False,
                message="Docker Desktop foi acionado, mas ainda nao terminou de iniciar.",
            )

        if self._containers_are_running():
            self._prepare_runtime_files()
            return EnvironmentCheck(
                status=EnvironmentStatus.READY,
                docker_installed=True,
                docker_running=True,
                compose_available=True,
                containers_running=True,
                message="Ambiente ja estava pronto e containers ativos.",
            )

        compose_path = self._prepare_runtime_files()
        failure = self._start_containers(compose_path)
        if failure is not None:
            return EnvironmentCheck(
                status=EnvironmentStatus.ERROR,
                docker_installed=True,
                docker_running=True,
                compose_available=True,
                containers_running=self._containers_are_running(),
                message=failure.headline,
                detail=failure.detail,
                action=failure.action,
                port=self.current_port(),
            )

        containers_running = self._wait_for_containers(self.CONTAINER_STARTUP_TIMEOUT_SECONDS)
        if containers_running:
            return EnvironmentCheck(
                status=EnvironmentStatus.READY,
                docker_installed=True,
                docker_running=True,
                compose_available=True,
                containers_running=True,
                message="Ambiente preparado e containers iniciados.",
                port=self.current_port(),
            )

        headline, detail = self._stopped_containers_message(compose_path)
        return EnvironmentCheck(
            status=EnvironmentStatus.ERROR,
            docker_installed=True,
            docker_running=True,
            compose_available=True,
            containers_running=False,
            message=headline,
            detail=detail,
            action=(
                "Clique em Ver detalhes tecnicos para ver o log do servico que "
                "falhou, e em Copiar detalhes para enviar ao suporte."
            ),
            port=self.current_port(),
        )

    def _start_containers(self, compose_path: Path):
        """Sobe os containers, contornando sozinho o que da para contornar.

        Uma porta reservada pelo Windows nao se resolve repetindo o mesmo
        comando: e preciso escolher outra porta antes de tentar de novo. Como o
        sistema tem essa informacao, ele faz isso sem perguntar nada ao usuario.
        """
        for attempt in range(self.START_ATTEMPTS):
            try:
                self._compose_pull(compose_path)
                self._compose_up(compose_path)
                return None
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                failure = classify(exc)
                last_attempt = attempt == self.START_ATTEMPTS - 1
                if not failure.can_retry_automatically or last_attempt:
                    return failure

                logger.warning(
                    "Preparo contornando %s: escolhendo outra porta para a Evolution",
                    failure.kind,
                )
                self._reassign_port(compose_path, blocked=failure.port)

        return None

    def _reassign_port(self, compose_path: Path, blocked: int | None) -> None:
        env_path = compose_path.parent / ".env"
        values = self._read_env(env_path)
        candidate = self.port_allocator.allocate()
        if blocked is not None and candidate == blocked:
            # O alocador nao viu a reserva (a lista do Windows nem sempre a
            # mostra): forcamos a proxima candidata.
            candidate = self.port_allocator.allocate(preferred=blocked + 10)

        values["EVOLUTION_PORT"] = str(candidate)
        self._write_env(env_path, values)
        self._apply_port(candidate)

    def sync_settings_from_runtime(self) -> int | None:
        """Realinha a URL da Evolution com a porta gravada em disco.

        O backend reinicia sem passar pelo preparo. Sem isto ele voltava
        apontando para a 8080 enquanto a Evolution estava publicada noutra
        porta, e a interface inteira acusava "offline".
        """
        port = self.current_port()
        if port is not None:
            self._apply_port(port)
        return port

    def current_port(self) -> int | None:
        return read_port_from_env(self.runtime_root / "docker" / ".env")

    def _apply_port(self, port: int) -> None:
        """A URL da Evolution tem de acompanhar a porta escolhida."""
        settings.EVOLUTION_PORT = port
        settings.EVOLUTION_BASE_URL = f"http://localhost:{port}"

    def runtime_compose_path(self) -> Path:
        return self.runtime_root / "docker" / "docker-compose.yml"

    def _prepare_runtime_files(self) -> Path:
        compose_source = self._source_compose_path()
        if not compose_source.exists():
            raise FileNotFoundError("docker-compose.yml nao encontrado.")

        docker_directory = self.runtime_root / "docker"
        docker_directory.mkdir(parents=True, exist_ok=True)
        compose_target = docker_directory / "docker-compose.yml"
        shutil.copy2(compose_source, compose_target)
        self._ensure_runtime_env(docker_directory / ".env")
        return compose_target

    def _ensure_runtime_env(self, env_path: Path) -> None:
        values = self._read_env(env_path)
        api_key = values.get("EVOLUTION_API_KEY") or settings.EVOLUTION_API_KEY
        if not api_key:
            api_key = secrets.token_urlsafe(32)
        values["EVOLUTION_API_KEY"] = api_key

        # A porta escolhida numa execucao anterior tem prioridade: trocar a
        # porta de quem ja funciona quebraria a URL da Evolution e o pareamento
        # do WhatsApp.
        existing_port = read_port_from_env(env_path)
        port = existing_port or self.port_allocator.allocate(preferred=settings.EVOLUTION_PORT)
        values["EVOLUTION_PORT"] = str(port)

        self._write_env(env_path, values)
        settings.EVOLUTION_API_KEY = api_key
        self._apply_port(port)

    def _write_env(self, env_path: Path, values: dict[str, str]) -> None:
        env_content = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
        env_path.write_text(f"{env_content}\n", encoding="utf-8")

    def _read_env(self, env_path: Path) -> dict[str, str]:
        if not env_path.exists():
            return {}

        values: dict[str, str] = {}
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            values[key.strip()] = value.strip()
        return values

    def _source_compose_path(self) -> Path:
        if getattr(sys, "frozen", False):
            bundled_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
            bundled_compose = bundled_root / "docker" / "docker-compose.yml"
            if bundled_compose.exists():
                return bundled_compose

        return Path(__file__).resolve().parents[2] / "docker" / "docker-compose.yml"

    #: Baixar Postgres, Redis e Evolution passa de 1 GB. Numa instalacao nova,
    #: com internet modesta, isso leva bem mais que os 3 minutos que o timeout
    #: antigo permitia — e o compose morria no meio, deixando os containers em
    #: "Created" sem nunca iniciar.
    PULL_TIMEOUT_SECONDS = 3600
    COMPOSE_UP_TIMEOUT_SECONDS = 900

    def _compose_pull(self, compose_path: Path) -> None:
        """Baixa as imagens antes de subir.

        Separar o download do `up` deixa o passo demorado isolado e retomavel:
        o Docker nao rebaixa camadas que ja vieram.
        """
        self._run(
            self._compose_command(compose_path, ["pull"]),
            cwd=compose_path.parent,
            check=False,
            timeout=self.PULL_TIMEOUT_SECONDS,
        )

    def _compose_up(self, compose_path: Path) -> None:
        self._run(
            self._compose_command(compose_path, ["up", "-d"]),
            cwd=compose_path.parent,
            timeout=self.COMPOSE_UP_TIMEOUT_SECONDS,
        )

    def _compose_command(self, compose_path: Path, action: list[str]) -> list[str]:
        return [
            "docker",
            "compose",
            "-f",
            str(compose_path),
            "--project-name",
            "ykmedia",
            *action,
        ]

    #: `compose up -d` devolve o controle assim que os containers sao criados,
    #: nao quando sobem. Postgres e Redis precisam inicializar o volume e a
    #: Evolution roda as migracoes: numa maquina modesta isso passa de um minuto.
    #: Uma retentativa basta: a segunda ja sai com a porta trocada. Repetir
    #: alem disso so esconderia um problema diferente.
    START_ATTEMPTS = 2
    CONTAINER_STARTUP_TIMEOUT_SECONDS = 180
    CONTAINER_POLL_SECONDS = 3

    def _wait_for_containers(self, timeout_seconds: int) -> bool:
        deadline = time.monotonic() + timeout_seconds
        while True:
            if self._containers_are_running():
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(self.CONTAINER_POLL_SECONDS)

    def _containers_are_running(self) -> bool:
        result = self._run(
            ["docker", "ps", "--format", "{{.Names}}"],
            check=False,
            timeout=20,
        )
        running_names = set(result.stdout.splitlines())
        return self._CONTAINER_NAMES.issubset(running_names)

    def _docker_is_running(self) -> bool:
        result = self._run(["docker", "info"], check=False, timeout=20)
        return result.returncode == 0

    def _command_exists(self, command: str) -> bool:
        return shutil.which(command) is not None

    def _install_docker_desktop(self) -> None:
        if not self._command_exists("winget"):
            return

        self._run(
            [
                "winget",
                "install",
                "--id",
                "Docker.DockerDesktop",
                "--exact",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
            ],
            check=False,
            timeout=900,
        )

    def _start_docker_desktop(self) -> None:
        possible_paths = [
            Path(os.environ.get("ProgramFiles", "")) / "Docker" / "Docker" / "Docker Desktop.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Docker" / "Docker Desktop.exe",
        ]

        for path in possible_paths:
            if path.exists():
                subprocess.Popen([str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return

    def _wait_for_docker(self, timeout_seconds: int) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self._docker_is_running():
                return
            time.sleep(3)

    def _run(
        self,
        command: list[str],
        cwd: Path | None = None,
        check: bool = True,
        timeout: int = 30,
    ) -> subprocess.CompletedProcess[str]:
        options: dict[str, object] = {
            "cwd": str(cwd) if cwd is not None else None,
            "capture_output": True,
            "text": True,
            # O Docker escreve UTF-8. Sem isto o Python usava a pagina de codigo
            # do Windows e "permissoes" chegava como "permissAues" na tela.
            "encoding": "utf-8",
            "errors": "replace",
            "check": check,
            "timeout": timeout,
        }
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW

        return self.command_runner(
            command,
            **options,
        )

    def _format_command_error(
        self,
        error: subprocess.CalledProcessError | subprocess.TimeoutExpired,
    ) -> str:
        if isinstance(error, subprocess.TimeoutExpired):
            return (
                "O download dos componentes demorou demais e foi interrompido. "
                "Verifique a internet e clique novamente: o Docker retoma de onde parou."
            )

        stderr = str(error.stderr or "").strip()
        stdout = str(error.stdout or "").strip()
        detail = stderr or stdout or str(error)
        return f"Falha ao executar Docker Compose: {detail}"

    def container_states(self, compose_path: Path) -> list[ContainerState]:
        """Estado de cada servico, em vez de um unico "deu errado".

        Na maquina do usuario o Postgres e o Redis subiram saudaveis e so a
        Evolution falhou; a tela dizia apenas "Ambiente: ERROR", como se nada
        tivesse funcionado.
        """
        result = self._run(
            self._compose_command(compose_path, ["ps", "--all", "--format", "json"]),
            cwd=compose_path.parent,
            check=False,
            timeout=30,
        )
        return self._parse_container_states(str(getattr(result, "stdout", "") or ""))

    def _parse_container_states(self, output: str) -> list[ContainerState]:
        stripped = output.strip()
        if not stripped:
            return []

        # Versoes recentes do Compose emitem um objeto por linha; as anteriores,
        # um array unico. Aceitamos os dois formatos.
        try:
            parsed = json.loads(stripped)
            entries = parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            entries = []
            for line in stripped.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        states: list[ContainerState] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            states.append(
                ContainerState(
                    name=str(entry.get("Name", "")),
                    service=str(entry.get("Service", "")),
                    state=str(entry.get("State", "")),
                    health=str(entry.get("Health", "") or ""),
                    exit_code=int(entry.get("ExitCode", 0) or 0),
                )
            )
        return states

    def _stopped_containers_message(self, compose_path: Path) -> tuple[str, str]:
        """Devolve (manchete, detalhe) descrevendo o que subiu e o que nao."""
        states = self.container_states(compose_path)
        if not states:
            return (
                "Docker Compose executou, mas nem todos os containers ficaram ativos.",
                "",
            )

        healthy = [state for state in states if state.is_up]
        broken = [state for state in states if not state.is_up]
        names = ", ".join(state.name or state.service for state in broken)
        headline = (
            f"{len(healthy)} de {len(states)} servicos subiram. "
            f"Nao ficou de pe: {names}."
        )

        # So o log de quem falhou: puxar os tres seria lento e enterraria o que
        # importa no meio de milhares de linhas.
        details = [
            "\n".join(f"{state.name}: {state.state} {state.health}".strip() for state in states)
        ]
        for state in broken:
            if not state.service:
                continue
            log = self._container_log(compose_path, state.service)
            if log:
                details.append(f"--- {state.name} ---\n{log}")

        return headline, "\n\n".join(details).strip()

    def _container_log(self, compose_path: Path, service: str) -> str:
        result = self._run(
            self._compose_command(compose_path, ["logs", "--tail", "20", service]),
            cwd=compose_path.parent,
            check=False,
            timeout=30,
        )
        stdout = str(getattr(result, "stdout", "") or "").strip()
        stderr = str(getattr(result, "stderr", "") or "").strip()
        return _ANSI.sub("", stdout or stderr)

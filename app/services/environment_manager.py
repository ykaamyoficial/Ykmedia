import os
import secrets
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from app.core.config import settings


class EnvironmentStatus(StrEnum):
    READY = "PRONTO"
    DOCKER_MISSING = "DOCKER_NAO_INSTALADO"
    DOCKER_STOPPED = "DOCKER_PARADO"
    CONFIG_MISSING = "CONFIGURACAO_PENDENTE"
    ERROR = "ERRO"


@dataclass(frozen=True, slots=True)
class EnvironmentCheck:
    status: EnvironmentStatus
    docker_installed: bool
    docker_running: bool
    compose_available: bool
    containers_running: bool
    message: str


class EnvironmentManager:
    _CONTAINER_NAMES = {"ykmedia_evolution", "ykmedia_postgres", "ykmedia_redis"}

    def __init__(
        self,
        runtime_root: str | Path | None = None,
        command_runner=subprocess.run,
    ) -> None:
        self.runtime_root = Path(
            runtime_root or Path(os.environ.get("LOCALAPPDATA", ".")) / "YkMedia"
        ).resolve()
        self.command_runner = command_runner

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
        try:
            self._compose_pull(compose_path)
            self._compose_up(compose_path)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            # TimeoutExpired nao era capturado aqui: numa instalacao nova o
            # download das imagens estourava o limite, a excecao subia ate virar
            # erro 500 e o usuario via apenas "Nao foi possivel preparar o
            # sistema", com os containers parados em "Created".
            return EnvironmentCheck(
                status=EnvironmentStatus.ERROR,
                docker_installed=True,
                docker_running=True,
                compose_available=True,
                containers_running=self._containers_are_running(),
                message=self._format_command_error(exc),
            )

        containers_running = self._wait_for_containers(self.CONTAINER_STARTUP_TIMEOUT_SECONDS)

        return EnvironmentCheck(
            status=EnvironmentStatus.READY if containers_running else EnvironmentStatus.ERROR,
            docker_installed=True,
            docker_running=True,
            compose_available=True,
            containers_running=containers_running,
            message="Ambiente preparado e containers iniciados."
            if containers_running
            else self._stopped_containers_message(compose_path),
        )

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
        env_content = "\n".join(f"{key}={value}" for key, value in sorted(values.items()))
        env_path.write_text(f"{env_content}\n", encoding="utf-8")
        settings.EVOLUTION_API_KEY = api_key

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

    def _stopped_containers_message(self, compose_path: Path) -> str:
        """Diz qual container ficou parado e por que, em vez de so falhar."""
        result = self._run(
            self._compose_command(compose_path, ["ps", "--all", "--format", "{{.Name}} {{.Status}}"]),
            cwd=compose_path.parent,
            check=False,
            timeout=30,
        )
        detail = str(getattr(result, "stdout", "") or "").strip()
        if not detail:
            return "Docker Compose executou, mas nem todos os containers ficaram ativos."

        return (
            "Docker Compose executou, mas nem todos os containers ficaram ativos:\n"
            f"{detail}"
        )

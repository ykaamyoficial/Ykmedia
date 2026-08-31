import subprocess
from pathlib import Path

from app.core.config import settings
from app.services.environment_manager import EnvironmentManager, EnvironmentStatus


class FakeCommandRunner:
    def __init__(self, docker_running: bool = True, containers_running: bool = True) -> None:
        self.docker_running = docker_running
        self.containers_running = containers_running
        self.commands: list[list[str]] = []

    def __call__(
        self,
        command: list[str],
        cwd: str | None = None,
        capture_output: bool = True,
        text: bool = True,
        check: bool = True,
        timeout: int = 30,
        **_: object,
    ) -> subprocess.CompletedProcess[str]:
        self.commands.append(command)
        if command[:2] == ["docker", "info"]:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0 if self.docker_running else 1,
                stdout="ok" if self.docker_running else "",
                stderr="" if self.docker_running else "not running",
            )

        if command[:2] == ["docker", "ps"]:
            stdout = (
                "ykmedia_evolution\nykmedia_postgres\nykmedia_redis\n"
                if self.containers_running
                else "ykmedia_postgres\n"
            )
            return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")

        if command[:2] == ["docker", "compose"]:
            self.containers_running = True
            return subprocess.CompletedProcess(args=command, returncode=0, stdout="started", stderr="")

        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")


def test_environment_check_reports_missing_docker(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.environment_manager.shutil.which", lambda command: None)
    manager = EnvironmentManager(runtime_root=tmp_path, command_runner=FakeCommandRunner())

    result = manager.check()

    assert result.status is EnvironmentStatus.DOCKER_MISSING
    assert result.docker_installed is False


def test_environment_check_reports_ready_containers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.environment_manager.shutil.which", lambda command: "docker")
    manager = EnvironmentManager(runtime_root=tmp_path, command_runner=FakeCommandRunner())

    result = manager.check()

    assert result.status is EnvironmentStatus.READY
    assert result.containers_running is True


def test_environment_prepare_copies_compose_and_starts_containers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.environment_manager.shutil.which", lambda command: "docker")
    runner = FakeCommandRunner(containers_running=False)
    manager = EnvironmentManager(runtime_root=tmp_path, command_runner=runner)

    result = manager.prepare(install_docker=False)

    assert result.status is EnvironmentStatus.READY
    assert manager.runtime_compose_path().exists()
    assert (tmp_path / "docker" / ".env").exists()
    assert ["docker", "compose", "-f", str(manager.runtime_compose_path()), "--project-name", "ykmedia", "up", "-d"] in runner.commands


def test_environment_prepare_does_not_recreate_running_containers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("app.services.environment_manager.shutil.which", lambda command: "docker")
    runner = FakeCommandRunner(containers_running=True)
    manager = EnvironmentManager(runtime_root=tmp_path, command_runner=runner)

    result = manager.prepare(install_docker=False)

    assert result.status is EnvironmentStatus.READY
    assert result.message == "Ambiente ja estava pronto e containers ativos."
    assert not any(command[:2] == ["docker", "compose"] for command in runner.commands)


def test_download_timeout_becomes_a_readable_message_instead_of_crashing(tmp_path: Path) -> None:
    """Era a causa da instalacao travada numa maquina nova.

    Baixar Postgres, Redis e Evolution passa de 1 GB. O timeout antigo de 3
    minutos estourava, TimeoutExpired nao era capturado, a excecao virava erro
    500 e os containers ficavam parados em "Created".
    """
    def runner(command, **kwargs):
        if "pull" in command or "up" in command:
            raise subprocess.TimeoutExpired(cmd=command, timeout=900)
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="ok", stderr="")

    manager = EnvironmentManager(runtime_root=tmp_path / "runtime", command_runner=runner)

    check = manager.prepare(install_docker=False)

    assert check.status is EnvironmentStatus.ERROR
    assert "demorou demais" in check.message
    # A manchete diz o que houve; a acao, o que fazer. Sao campos distintos
    # para a tela nao precisar misturar os dois no mesmo paragrafo.
    assert "retoma de onde parou" in check.action


def test_images_are_pulled_before_starting_the_containers(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    started = {"value": False}

    def runner(command, **kwargs):
        calls.append(list(command))
        if command[:2] == ["docker", "compose"] and "up" in command:
            started["value"] = True
        if command[:2] == ["docker", "ps"]:
            stdout = "ykmedia_evolution\nykmedia_postgres\nykmedia_redis\n" if started["value"] else ""
        else:
            stdout = "ok"
        return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")

    manager = EnvironmentManager(runtime_root=tmp_path / "runtime", command_runner=runner)
    manager.prepare(install_docker=False)

    compose_actions = [c for c in calls if "compose" in c]
    pull_index = next((i for i, c in enumerate(compose_actions) if "pull" in c), None)
    up_index = next((i for i, c in enumerate(compose_actions) if "up" in c), None)

    # O download e a parte demorada: isolar num passo proprio deixa o `up`
    # rapido e o progresso retomavel.
    assert pull_index is not None, "faltou o docker compose pull"
    assert up_index is not None
    assert pull_index < up_index


def test_containers_get_time_to_finish_starting(tmp_path: Path, monkeypatch) -> None:
    """`compose up -d` retorna antes dos containers estarem de pe.

    Numa maquina mais lenta a Evolution ainda aparecia como "Created" na hora em
    que checavamos, e o preparo declarava ERRO num ambiente que ficaria pronto
    poucos segundos depois.
    """
    monkeypatch.setattr("app.services.environment_manager.time.sleep", lambda _: None)
    checks = {"count": 0}

    def runner(command, **kwargs):
        if command[:2] == ["docker", "ps"]:
            checks["count"] += 1
            # So na terceira consulta os tres containers aparecem rodando.
            stdout = (
                "ykmedia_evolution\nykmedia_postgres\nykmedia_redis\n"
                if checks["count"] >= 3
                else "ykmedia_postgres\n"
            )
            return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="ok", stderr="")

    manager = EnvironmentManager(runtime_root=tmp_path / "runtime", command_runner=runner)

    check = manager.prepare(install_docker=False)

    assert check.status is EnvironmentStatus.READY
    assert check.containers_running is True


PORT_RESERVED_STDERR = (
    "Container ykmedia_postgres Healthy\n"
    "Error response from daemon: ports are not available: exposing port "
    "TCP 0.0.0.0:8080 -> 127.0.0.1:0: listen tcp 0.0.0.0:8080: bind: "
    "proibida pelas permissoes de acesso."
)


def test_a_reserved_port_is_replaced_automatically(tmp_path: Path, monkeypatch) -> None:
    """Era o erro da maquina do usuario em 30/08.

    O Windows reserva faixas de portas com Hyper-V/WSL2 ativos e a faixa muda a
    cada reinicio. Com a 8080 fixa no compose a instalacao morria sem saida;
    agora o sistema escolhe outra porta e segue sozinho.
    """
    monkeypatch.setattr("app.services.environment_manager.time.sleep", lambda _: None)
    attempts = {"up": 0}

    def runner(command, **kwargs):
        if command[:2] == ["docker", "compose"] and "up" in command:
            attempts["up"] += 1
            if attempts["up"] == 1:
                raise subprocess.CalledProcessError(
                    returncode=1, cmd=command, output="", stderr=PORT_RESERVED_STDERR
                )
        if command[:2] == ["docker", "ps"]:
            stdout = (
                "ykmedia_evolution\nykmedia_postgres\nykmedia_redis\n"
                if attempts["up"] >= 2
                else ""
            )
            return subprocess.CompletedProcess(args=command, returncode=0, stdout=stdout, stderr="")
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="ok", stderr="")

    manager = EnvironmentManager(
        runtime_root=tmp_path / "runtime",
        command_runner=runner,
        port_allocator=_FixedPortAllocator(8090),
    )

    check = manager.prepare(install_docker=False)

    assert check.status is EnvironmentStatus.READY
    assert attempts["up"] == 2, "a segunda tentativa com a porta nova nao aconteceu"
    assert check.port == 8090
    env_content = (tmp_path / "runtime" / "docker" / ".env").read_text(encoding="utf-8")
    assert "EVOLUTION_PORT=8090" in env_content


def test_an_unknown_failure_is_not_retried_forever(tmp_path: Path) -> None:
    """So repetimos quando sabemos que a causa foi contornada."""

    def runner(command, **kwargs):
        if command[:2] == ["docker", "compose"] and "up" in command:
            raise subprocess.CalledProcessError(
                returncode=1, cmd=command, output="", stderr="Error response from daemon: algo novo"
            )
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    manager = EnvironmentManager(runtime_root=tmp_path / "runtime", command_runner=runner)

    check = manager.prepare(install_docker=False)

    assert check.status is EnvironmentStatus.ERROR
    assert "suporte" in check.action.lower()
    # O texto tecnico segue disponivel para o suporte, fora da manchete.
    assert "algo novo" in check.detail


def test_docker_output_is_decoded_as_utf8(tmp_path: Path) -> None:
    """Sem isto o Python usava a pagina de codigo do Windows e o portugues do
    Docker chegava como "permissAues" na tela."""
    captured: dict[str, object] = {}

    def runner(command, **kwargs):
        captured.update(kwargs)
        return subprocess.CompletedProcess(args=command, returncode=0, stdout="", stderr="")

    manager = EnvironmentManager(runtime_root=tmp_path / "runtime", command_runner=runner)
    manager._docker_is_running()

    assert captured.get("encoding") == "utf-8"
    assert captured.get("errors") == "replace"


class _FixedPortAllocator:
    def __init__(self, port: int) -> None:
        self._port = port

    def allocate(self, preferred: int | None = None) -> int:
        return self._port


def test_the_chosen_port_survives_a_restart(tmp_path: Path) -> None:
    """O backend reinicia sem passar pelo preparo.

    Sem reler a porta gravada, ele voltava apontando para a 8080 enquanto a
    Evolution estava publicada noutra porta -- e tudo respondia "offline".
    """
    docker_directory = tmp_path / "runtime" / "docker"
    docker_directory.mkdir(parents=True)
    (docker_directory / ".env").write_text("EVOLUTION_PORT=8090\n", encoding="utf-8")

    manager = EnvironmentManager(runtime_root=tmp_path / "runtime")
    manager.sync_settings_from_runtime()

    assert settings.EVOLUTION_PORT == 8090
    assert settings.EVOLUTION_BASE_URL == "http://localhost:8090"

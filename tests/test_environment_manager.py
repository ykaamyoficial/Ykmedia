import subprocess
from pathlib import Path

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
    assert "retoma de onde parou" in check.message


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

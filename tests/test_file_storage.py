import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from app.models.download import DownloadedMedia
from app.services.file_storage import (
    EmptyFileContentError,
    FileStorage,
    FileWriteError,
    InvalidFileNameError,
)


def _downloaded_media(
    content: bytes = b"conteudo",
    file_name: str | None = "arquivo.txt",
) -> DownloadedMedia:
    return DownloadedMedia(
        message_id="MSG1",
        content=content,
        mimetype="text/plain",
        size_bytes=len(content),
        file_name=file_name,
    )


def test_saves_file_successfully(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)

    result = storage.save(_downloaded_media())

    assert Path(result.absolute_path).read_bytes() == b"conteudo"
    assert result.relative_path == "arquivo.txt"
    assert result.file_name == "arquivo.txt"
    assert result.extension == ".txt"
    assert result.size_bytes == 8


def test_creates_directories_automatically(tmp_path: Path) -> None:
    root_directory = tmp_path / "media"
    storage = FileStorage(root_directory=root_directory)

    result = storage.save(_downloaded_media())

    assert root_directory.exists()
    assert Path(result.absolute_path).exists()


def test_calculates_sha256(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)
    content = b"hash-me"

    result = storage.save(_downloaded_media(content=content))

    assert result.sha256 == hashlib.sha256(content).hexdigest()


def test_rejects_empty_content(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)

    with pytest.raises(EmptyFileContentError):
        storage.save(_downloaded_media(content=b""))


def test_rejects_invalid_file_name(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)

    with pytest.raises(InvalidFileNameError):
        storage.save(_downloaded_media(file_name="../arquivo.txt"))


def test_rejects_file_name_with_invalid_characters(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)

    with pytest.raises(InvalidFileNameError):
        storage.save(_downloaded_media(file_name="arquivo?.txt"))


def test_uses_message_id_when_file_name_is_missing(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)

    result = storage.save(_downloaded_media(file_name=None))

    assert result.file_name == "MSG1"
    assert Path(result.absolute_path).read_bytes() == b"conteudo"


def test_raises_file_write_error(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)

    with patch.object(Path, "write_bytes", side_effect=OSError("write failed")):
        with pytest.raises(FileWriteError):
            storage.save(_downloaded_media())


def test_renames_stored_file_preserving_extension(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)
    stored_file = storage.save(_downloaded_media(file_name="original.txt"))

    renamed_file = storage.rename(stored_file, "novo_nome")

    assert Path(stored_file.absolute_path).exists() is False
    assert Path(renamed_file.absolute_path).exists() is True
    assert renamed_file.file_name == "novo_nome.txt"
    assert renamed_file.relative_path == "novo_nome.txt"
    assert renamed_file.sha256 == stored_file.sha256


def test_moves_file_to_existing_folder(tmp_path: Path) -> None:
    destination = tmp_path / "Louvores"
    destination.mkdir()
    storage = FileStorage(root_directory=tmp_path)
    stored_file = storage.save(_downloaded_media(file_name="original.txt"))

    moved_file = storage.move(stored_file, "Louvores", "louvor")

    assert Path(moved_file.relative_path) == Path("Louvores") / "louvor.txt"
    assert Path(moved_file.absolute_path).exists()
    assert Path(stored_file.absolute_path).exists() is False


def test_creates_destination_folder_automatically(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)
    stored_file = storage.save(_downloaded_media(file_name="original.txt"))

    moved_file = storage.move(stored_file, "Mensagens", "mensagem")

    assert (tmp_path / "Mensagens").exists()
    assert Path(moved_file.absolute_path).exists()


def test_move_preserves_original_extension(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)
    stored_file = storage.save(_downloaded_media(file_name="original.mp4"))

    moved_file = storage.move(stored_file, "Jovens", "culto_jovem")

    assert moved_file.file_name == "culto_jovem.mp4"
    assert moved_file.extension == ".mp4"


def test_move_generates_unique_name_when_file_exists(tmp_path: Path) -> None:
    storage = FileStorage(root_directory=tmp_path)
    first_file = storage.save(_downloaded_media(file_name="primeiro.txt"))
    second_file = storage.save(_downloaded_media(file_name="segundo.txt"))

    first_moved = storage.move(first_file, "Louvores", "louvor")
    second_moved = storage.move(second_file, "Louvores", "louvor")

    assert first_moved.file_name == "louvor.txt"
    assert second_moved.file_name == "louvor_1.txt"
    assert Path(second_moved.absolute_path).exists()

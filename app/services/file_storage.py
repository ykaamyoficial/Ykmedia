import hashlib
from pathlib import Path

from app.core.config import settings
from app.models.download import DownloadedMedia
from app.models.storage import StoredFile


class FileStorageError(Exception):
    """Base exception for file storage errors."""


class EmptyFileContentError(FileStorageError):
    """Raised when there is no content to write."""


class InvalidFileNameError(FileStorageError):
    """Raised when the file name is unsafe or invalid."""


class FileWriteError(FileStorageError):
    """Raised when the file cannot be written to disk."""


class FileStorage:
    _INVALID_FILE_NAME_CHARS = set('<>:"/\\|?*')

    def __init__(self, root_directory: str | Path | None = None) -> None:
        self.root_directory = Path(root_directory or settings.FILE_STORAGE_ROOT).resolve()

    def save(self, media: DownloadedMedia) -> StoredFile:
        if not media.content:
            raise EmptyFileContentError("Arquivo nao possui conteudo para gravacao.")

        file_name = self._resolve_file_name(media)
        target_path = self.root_directory / file_name

        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(media.content)
        except OSError as exc:
            raise FileWriteError("Falha ao gravar arquivo em disco.") from exc

        sha256 = hashlib.sha256(media.content).hexdigest()
        absolute_path = target_path.resolve()

        return StoredFile(
            absolute_path=str(absolute_path),
            relative_path=str(absolute_path.relative_to(self.root_directory)),
            file_name=file_name,
            extension=target_path.suffix,
            size_bytes=len(media.content),
            sha256=sha256,
        )

    def rename(self, stored_file: StoredFile, new_file_name: str) -> StoredFile:
        source_path = Path(stored_file.absolute_path).resolve()
        if not source_path.exists():
            raise FileWriteError("Arquivo original nao encontrado para renomeacao.")

        target_file_name = self._resolve_renamed_file_name(
            new_file_name=new_file_name,
            original_extension=stored_file.extension,
        )
        target_path = source_path.with_name(target_file_name)

        try:
            source_path.rename(target_path)
        except OSError as exc:
            raise FileWriteError("Falha ao renomear arquivo em disco.") from exc

        content = target_path.read_bytes()
        absolute_path = target_path.resolve()

        return StoredFile(
            absolute_path=str(absolute_path),
            relative_path=str(absolute_path.relative_to(self.root_directory)),
            file_name=target_file_name,
            extension=target_path.suffix,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    def move(
        self,
        stored_file: StoredFile,
        destination_folder: str,
        new_file_name: str,
    ) -> StoredFile:
        source_path = Path(stored_file.absolute_path).resolve()
        if not source_path.exists():
            raise FileWriteError("Arquivo original nao encontrado para movimentacao.")

        self._validate_file_name(destination_folder)
        target_file_name = self._resolve_renamed_file_name(
            new_file_name=new_file_name,
            original_extension=stored_file.extension,
        )
        destination_directory = self.root_directory / destination_folder
        target_path = self._resolve_unique_path(destination_directory / target_file_name)

        try:
            destination_directory.mkdir(parents=True, exist_ok=True)
            source_path.rename(target_path)
        except OSError as exc:
            raise FileWriteError("Falha ao mover arquivo em disco.") from exc

        content = target_path.read_bytes()
        absolute_path = target_path.resolve()

        return StoredFile(
            absolute_path=str(absolute_path),
            relative_path=str(absolute_path.relative_to(self.root_directory)),
            file_name=target_path.name,
            extension=target_path.suffix,
            size_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
        )

    def _resolve_file_name(self, media: DownloadedMedia) -> str:
        file_name = media.file_name or media.message_id
        self._validate_file_name(file_name)
        return file_name

    def _validate_file_name(self, file_name: str) -> None:
        if not file_name or file_name.strip() != file_name:
            raise InvalidFileNameError("Nome de arquivo invalido.")

        if any(character in self._INVALID_FILE_NAME_CHARS for character in file_name):
            raise InvalidFileNameError("Nome de arquivo contem caracteres invalidos.")

        file_path = Path(file_name)
        if file_path.name != file_name or file_name in {".", ".."}:
            raise InvalidFileNameError("Nome de arquivo nao pode conter caminho.")

    def _resolve_renamed_file_name(self, new_file_name: str, original_extension: str) -> str:
        self._validate_file_name(new_file_name)
        new_path = Path(new_file_name)
        if new_path.suffix:
            return new_file_name

        return f"{new_file_name}{original_extension}"

    def _resolve_unique_path(self, target_path: Path) -> Path:
        if not target_path.exists():
            return target_path

        suffix = target_path.suffix
        stem = target_path.stem
        parent = target_path.parent
        counter = 1

        while True:
            candidate = parent / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate

            counter += 1

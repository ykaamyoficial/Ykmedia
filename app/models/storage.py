from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StoredFile:
    absolute_path: str
    relative_path: str
    file_name: str
    extension: str
    size_bytes: int
    sha256: str

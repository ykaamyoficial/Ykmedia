from pydantic import BaseModel


class FileLibraryItem(BaseModel):
    id: str
    date: str
    date_display: str
    sender: str
    sender_raw: str
    origin: str
    category: str
    final_name: str
    file_path: str
    absolute_path: str
    kind: str
    status: str
    size: str
    exists: bool


class FileLibraryResponse(BaseModel):
    items: list[FileLibraryItem]
    total: int

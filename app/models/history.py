from pydantic import BaseModel


class HistoryItem(BaseModel):
    id: str
    date: str
    date_display: str
    sender: str
    sender_raw: str
    origin: str
    category: str
    final_name: str
    file_path: str
    kind: str
    status: str


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
    total: int

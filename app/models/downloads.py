from pydantic import BaseModel


class DownloadJobItem(BaseModel):
    id: str
    short_id: str
    sender: str
    sender_raw: str
    origin: str
    file: str
    kind: str
    status: str
    created_at: str


class DownloadJobsResponse(BaseModel):
    items: list[DownloadJobItem]
    total: int


class ClearCompletedDownloadsResponse(BaseModel):
    removed: int

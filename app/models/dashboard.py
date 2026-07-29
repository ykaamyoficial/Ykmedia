from pydantic import BaseModel


class DashboardHealthItem(BaseModel):
    key: str
    label: str
    status: str
    description: str


class DashboardSystemInfo(BaseModel):
    version: str
    uptime_seconds: int
    backend_online: bool
    database_connected: bool


class DashboardEvolutionInfo(BaseModel):
    online: bool
    instance: str
    last_sync: str | None = None
    error: str | None = None


class DashboardWhatsAppInfo(BaseModel):
    status: str
    connected: bool
    qr_pending: bool


class DashboardDownloadsInfo(BaseModel):
    in_progress: int
    completed: int
    failures: int
    queue: int


class DashboardFilesInfo(BaseModel):
    stored_count: int
    storage_used_bytes: int
    categories: list[str]


class DashboardConversationMessage(BaseModel):
    sender: str
    last_content: str | None = None
    last_activity: str | None = None
    status: str
    message_count: int


class DashboardConversationsInfo(BaseModel):
    total: int
    active_contacts: int
    latest_messages: list[DashboardConversationMessage]


class DashboardHistoryItem(BaseModel):
    id: str
    date: str
    sender: str
    origin: str
    category: str | None = None
    final_name: str | None = None
    file_path: str | None = None
    status: str


class DashboardOverview(BaseModel):
    generated_at: str
    system: DashboardSystemInfo
    evolution: DashboardEvolutionInfo
    whatsapp: DashboardWhatsAppInfo
    downloads: DashboardDownloadsInfo
    files: DashboardFilesInfo
    conversations: DashboardConversationsInfo
    history: list[DashboardHistoryItem]
    health: list[DashboardHealthItem]
    has_data: bool

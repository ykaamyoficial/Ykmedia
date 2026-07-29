from pydantic import BaseModel


class AppSettingsResponse(BaseModel):
    downloads_root: str
    ffmpeg_path: str
    sqlite_database: str
    whatsapp_instance: str
    evolution_state: str
    evolution_message: str


class SaveAppSettingsRequest(BaseModel):
    downloads_root: str
    ffmpeg_path: str
    sqlite_database: str
    whatsapp_instance: str


class EvolutionSessionResponse(BaseModel):
    instance_name: str
    state: str
    message: str
    qrcode_base64: str | None = None


class DiagnosticItemResponse(BaseModel):
    key: str
    name: str
    status: str
    message: str


class DiagnosticReportResponse(BaseModel):
    status: str
    message: str
    items: list[DiagnosticItemResponse]


class SetupStepResponse(BaseModel):
    key: str
    label: str
    status: str
    message: str


class SetupReportResponse(BaseModel):
    status: str
    message: str
    steps: list[SetupStepResponse]

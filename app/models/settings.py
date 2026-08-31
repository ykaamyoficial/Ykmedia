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
    #: `message` e a manchete; `detail` guarda o log tecnico do Docker e
    #: `action` diz o que fazer. Separados para a tela nao empilhar os tres no
    #: mesmo paragrafo, como acontecia ate a 0.4.1.
    message: str
    detail: str = ""
    action: str = ""


class SetupProgressResponse(BaseModel):
    """Instantaneo do preparo em curso, consultado pela tela a cada segundo."""

    running: bool
    status: str
    message: str
    steps: list["SetupStepResponse"]


class SetupReportResponse(BaseModel):
    status: str
    message: str
    steps: list[SetupStepResponse]


class EvolutionLicenseResponse(BaseModel):
    status: str
    register_url: str | None = None
    message: str = ""

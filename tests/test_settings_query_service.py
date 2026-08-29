from app.models.settings import EvolutionSessionResponse
from app.services.configuration_manager import SetupStepResult, SetupStepStatus
from app.services.evolution_client import EvolutionHttpError
from app.services.settings_query_service import SettingsQueryService


class MissingInstanceClient:
    def __init__(self) -> None:
        self.connect_attempts = 0

    async def connect_instance(self) -> dict[str, object]:
        self.connect_attempts += 1
        if self.connect_attempts == 1:
            raise EvolutionHttpError(404, "Evolution API returned HTTP 404.")
        return {"instance": {"state": "connecting"}, "qrcode": {"base64": "qr-image"}}


class SuccessfulProvisioning:
    def __init__(self) -> None:
        self.calls = 0

    def provision(self) -> SetupStepResult:
        self.calls += 1
        return SetupStepResult("evolution", "Evolution", SetupStepStatus.OK, "Instancia criada.")


def test_connect_recreates_missing_instance_before_requesting_qr_code() -> None:
    client = MissingInstanceClient()
    provisioning = SuccessfulProvisioning()
    service = SettingsQueryService(
        configuration_manager=object(),
        diagnostic_service=object(),
        automatic_setup_service=object(),
        evolution_provisioning_manager=provisioning,  # type: ignore[arg-type]
        evolution_client=client,
    )

    result: EvolutionSessionResponse = service.connect_evolution_session()

    assert provisioning.calls == 1
    assert client.connect_attempts == 2
    assert result.state == "connecting"
    assert result.qrcode_base64 == "qr-image"

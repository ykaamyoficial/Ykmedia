from fastapi import APIRouter, Depends

from app.models.history import HistoryResponse
from app.services.application_factory import get_history_query_service
from app.services.history_query_service import HistoryQueryService

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryResponse)
def list_history(
    service: HistoryQueryService = Depends(get_history_query_service),
) -> HistoryResponse:
    return service.list_history()

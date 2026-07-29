from fastapi import APIRouter, Depends

from app.models.files import FileLibraryResponse
from app.services.application_factory import get_file_query_service
from app.services.file_query_service import FileQueryService

router = APIRouter(prefix="/files", tags=["files"])


@router.get("", response_model=FileLibraryResponse)
def list_files(
    service: FileQueryService = Depends(get_file_query_service),
) -> FileLibraryResponse:
    return service.list_files()

from fastapi import APIRouter, Depends

from app.models.downloads import ClearCompletedDownloadsResponse, DownloadJobsResponse
from app.services.application_factory import get_download_query_service
from app.services.download_query_service import DownloadQueryService

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.get("/jobs", response_model=DownloadJobsResponse)
def list_download_jobs(
    service: DownloadQueryService = Depends(get_download_query_service),
) -> DownloadJobsResponse:
    return service.list_jobs()


@router.delete("/jobs/completed", response_model=ClearCompletedDownloadsResponse)
def clear_completed_download_jobs(
    service: DownloadQueryService = Depends(get_download_query_service),
) -> ClearCompletedDownloadsResponse:
    return service.clear_completed()

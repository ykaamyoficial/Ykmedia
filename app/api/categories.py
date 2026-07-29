from fastapi import APIRouter, Depends, HTTPException

from app.models.categories import CategoriesResponse, SaveCategoriesRequest
from app.services.application_factory import get_category_query_service
from app.services.category_query_service import CategoryQueryService
from app.services.category_service import CategoryServiceError

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=CategoriesResponse)
def list_categories(
    service: CategoryQueryService = Depends(get_category_query_service),
) -> CategoriesResponse:
    return service.list_categories()


@router.put("", response_model=CategoriesResponse)
def save_categories(
    request: SaveCategoriesRequest,
    service: CategoryQueryService = Depends(get_category_query_service),
) -> CategoriesResponse:
    try:
        return service.save_categories(request.categories)
    except (CategoryServiceError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

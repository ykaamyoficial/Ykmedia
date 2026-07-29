from pydantic import BaseModel


class CategoryItem(BaseModel):
    position: int
    name: str
    folder: str


class CategoriesResponse(BaseModel):
    items: list[CategoryItem]
    total: int


class SaveCategoriesRequest(BaseModel):
    categories: list[str]

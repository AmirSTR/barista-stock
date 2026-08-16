from typing import Dict, List
from pydantic import BaseModel, ConfigDict, Field


class CatalogProductItem(BaseModel):
    id: int
    name: str
    sku: str
    category: str
    unit: str
    available_qty: float = Field(..., description="Available quantity in warehouse (real_qty - reserved_qty)")
    is_stop: bool = Field(..., description="True if available_qty <= 0")

    model_config = ConfigDict(from_attributes=True)


class CatalogCategoryGroup(BaseModel):
    category: str
    items_count: int
    items: List[CatalogProductItem]


class CatalogResponse(BaseModel):
    total_categories: int
    total_products: int
    categories: List[CatalogCategoryGroup]

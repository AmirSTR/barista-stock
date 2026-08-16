from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.catalog import CatalogResponse
from app.services.catalog_service import CatalogService

router = APIRouter()


@router.get("", response_model=CatalogResponse, summary="Get full product catalog grouped by 8 categories")
@router.get("/", response_model=CatalogResponse, include_in_schema=False)
async def get_catalog(db: AsyncSession = Depends(get_db)):
    """Returns all active products grouped by 8 coffee chain categories.

    Each product contains: id, name, sku, category, unit, available_qty, is_stop.
    """
    return await CatalogService.get_grouped_catalog(db)

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_admin_api_key
from app.core.database import get_db
from app.models.bar import Bar
from app.schemas.bar import BarCreate, BarResponse, BarUpdate

router = APIRouter()


@router.get("/", response_model=List[BarResponse], summary="List all coffee bars")
async def list_bars(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
):
    query = select(Bar)
    if is_active is not None:
        query = query.where(Bar.is_active == is_active)
    query = query.order_by(Bar.id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post(
    "/",
    response_model=BarResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a coffee bar",
    dependencies=[Depends(require_admin_api_key)],
)
async def create_bar(
    bar_in: BarCreate,
    db: AsyncSession = Depends(get_db),
):
    bar = Bar(
        name=bar_in.name,
        telegram_chat_id=bar_in.telegram_chat_id,
        is_active=bar_in.is_active,
    )
    db.add(bar)
    await db.commit()
    await db.refresh(bar)
    return bar


@router.get("/{bar_id}", response_model=BarResponse, summary="Get coffee bar details")
async def get_bar(
    bar_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bar).where(Bar.id == bar_id))
    bar = result.scalar_one_or_none()
    if not bar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bar with ID {bar_id} not found")
    return bar


@router.patch(
    "/{bar_id}",
    response_model=BarResponse,
    summary="Update coffee bar",
    dependencies=[Depends(require_admin_api_key)],
)
async def update_bar(
    bar_id: int,
    bar_in: BarUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bar).where(Bar.id == bar_id))
    bar = result.scalar_one_or_none()
    if not bar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bar with ID {bar_id} not found")

    update_data = bar_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(bar, field, val)

    await db.commit()
    await db.refresh(bar)
    return bar


@router.delete(
    "/{bar_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete coffee bar",
    dependencies=[Depends(require_admin_api_key)],
)
async def delete_bar(
    bar_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Bar).where(Bar.id == bar_id))
    bar = result.scalar_one_or_none()
    if not bar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bar with ID {bar_id} not found")

    await db.delete(bar)
    await db.commit()
    return None

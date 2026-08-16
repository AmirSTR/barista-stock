from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, computed_field


class StockBase(BaseModel):
    product_id: int
    real_qty: float = Field(default=0.0, ge=0.0, description="Actual physical stock quantity in warehouse")
    reserved_qty: float = Field(default=0.0, ge=0.0, description="Quantity reserved for pending/packing orders")


class StockUpdate(BaseModel):
    real_qty: Optional[float] = Field(None, ge=0.0)
    reserved_qty: Optional[float] = Field(None, ge=0.0)


class StockAdjustment(BaseModel):
    delta_real_qty: Optional[float] = Field(0.0, description="Add or subtract from real_qty")
    delta_reserved_qty: Optional[float] = Field(0.0, description="Add or subtract from reserved_qty")


class StockResponse(BaseModel):
    id: int
    product_id: int
    real_qty: float
    reserved_qty: float
    available_qty: float

    model_config = ConfigDict(from_attributes=True)

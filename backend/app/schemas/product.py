from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.stock import StockResponse


class ProductBase(BaseModel):
    sku: str = Field(..., max_length=50, description="Unique SKU code, e.g. SKU-0001")
    name: str = Field(..., max_length=255, description="Product title")
    category: str = Field(..., max_length=100, description="Product category")
    unit: str = Field(..., max_length=50, description="Unit of measurement (шт, кг, л, etc.)")
    is_active: bool = Field(True, description="Whether the product is currently active")


class ProductCreate(ProductBase):
    initial_real_qty: Optional[float] = Field(0.0, ge=0.0, description="Initial real quantity for stock")


class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, max_length=50)
    name: Optional[str] = Field(None, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ProductWithStockResponse(ProductResponse):
    stock: Optional[StockResponse] = None

    model_config = ConfigDict(from_attributes=True)

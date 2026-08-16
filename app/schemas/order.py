from datetime import datetime
from typing import List, Optional
from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.models.order import OrderStatus
from app.schemas.product import ProductResponse


class OrderItemInput(BaseModel):
    product_id: int = Field(..., description="ID of the product to order")
    quantity: float = Field(
        ...,
        gt=0.0,
        validation_alias=AliasChoices("quantity", "requested_qty"),
        description="Quantity requested",
    )


class OrderItemCreate(BaseModel):
    product_id: int
    requested_qty: float = Field(
        ...,
        gt=0.0,
        validation_alias=AliasChoices("requested_qty", "quantity"),
    )


class OrderItemUpdate(BaseModel):
    confirmed_qty: Optional[float] = Field(None, ge=0.0)


class OrderItemBase(BaseModel):
    product_id: int
    requested_qty: float
    confirmed_qty: Optional[float] = None


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    bar_id: int
    items: List[OrderItemCreate] = Field(..., min_length=1, description="List of items in the order")


class OrderCreateRequest(BaseModel):
    bar_id: int
    items: List[OrderItemInput] = Field(..., min_length=1, description="List of items to order")


class OrderConfirmedItem(BaseModel):
    id: int
    product_id: int
    name: str
    sku: str
    unit: str
    requested_qty: float
    confirmed_qty: float


class PartialItemWarning(BaseModel):
    product_id: int
    name: str
    sku: str
    requested_qty: float
    confirmed_qty: float
    available_before: float
    message: str


class OutOfStockItemWarning(BaseModel):
    product_id: int
    name: str
    sku: str
    requested_qty: float
    available_before: float
    message: str


class OrderCreateResultResponse(BaseModel):
    id: int = Field(..., description="Order ID")
    order_id: int = Field(..., description="Order ID (alias)")
    bar_id: int
    status: OrderStatus
    created_at: datetime
    items: List[OrderConfirmedItem]
    partial_items: List[PartialItemWarning]
    out_of_stock_items: List[OutOfStockItemWarning]

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    items_confirmation: Optional[List[OrderItemUpdate]] = None


class OrderResponse(BaseModel):
    id: int
    bar_id: int
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

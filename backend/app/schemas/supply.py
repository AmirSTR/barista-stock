from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.supply import SupplyStatus
from app.schemas.product import ProductResponse


class SupplyItemBase(BaseModel):
    detected_name: str = Field(..., max_length=255, description="Recognized item name from invoice OCR")
    quantity: float = Field(..., gt=0.0, description="Recognized quantity")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="OCR confidence score from 0.0 to 1.0")
    product_id: Optional[int] = Field(None, description="Linked catalog product ID (if matched)")


class SupplyItemCreate(SupplyItemBase):
    pass


class SupplyItemUpdate(BaseModel):
    product_id: Optional[int] = None
    quantity: Optional[float] = Field(None, gt=0.0)
    detected_name: Optional[str] = None


class SupplyItemResponse(SupplyItemBase):
    id: int
    invoice_id: int
    product: Optional[ProductResponse] = None

    model_config = ConfigDict(from_attributes=True)


class SupplyInvoiceCreate(BaseModel):
    photo_file_id: str = Field(..., max_length=255, description="Telegram / Storage file ID of invoice photo")
    invoice_number: Optional[str] = Field(None, max_length=100, description="Document/invoice number")
    items: List[SupplyItemCreate] = Field(default=[], description="Detected invoice line items")


class SupplyInvoiceResponse(BaseModel):
    id: int
    photo_file_id: str
    invoice_number: Optional[str] = None
    status: SupplyStatus
    created_at: datetime
    items: List[SupplyItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

from typing import List, Optional
from pydantic import BaseModel, Field


class InvoiceItemOCR(BaseModel):
    """Line item extracted from invoice photo by Vision LLM."""
    raw_name: str = Field(..., description="Наименование товара как в накладной/чеке")
    quantity: float = Field(..., gt=0.0, description="Количество товара")
    unit: str = Field(default="шт", description="Единица измерения (шт, уп, кг, бут, л, и т.д.)")


class InvoiceOCRResponse(BaseModel):
    """Structured response parsed from invoice image via Vision LLM."""
    invoice_number: Optional[str] = Field(default=None, description="Номер документа или null")
    items: List[InvoiceItemOCR] = Field(default_factory=list, description="Список товарных позиций")


class MatchedSupplyItem(BaseModel):
    """Result of matching an OCR line item against database product catalog."""
    raw_name: str
    quantity: float
    unit: str
    product_id: Optional[int] = None
    product_name: Optional[str] = None
    confidence_score: float = 0.0  # 0.0 to 1.0 (e.g. 0.94 for 94%)
    is_uncertain: bool = False

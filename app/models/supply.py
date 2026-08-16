import enum
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product import Product


class SupplyStatus(str, enum.Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class SupplyInvoice(Base):
    __tablename__ = "supply_invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    photo_file_id: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_number: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[SupplyStatus] = mapped_column(
        Enum(SupplyStatus),
        default=SupplyStatus.DRAFT,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    items: Mapped[List["SupplyItem"]] = relationship(
        "SupplyItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<SupplyInvoice(id={self.id}, status='{self.status.value}')>"


class SupplyItem(Base):
    __tablename__ = "supply_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("supply_invoices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("products.id"),
        nullable=True,
        index=True,
    )
    detected_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_uncertain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    invoice: Mapped["SupplyInvoice"] = relationship(
        "SupplyInvoice", back_populates="items", lazy="selectin"
    )
    product: Mapped[Optional["Product"]] = relationship(
        "Product", back_populates="supply_items", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<SupplyItem(id={self.id}, detected_name='{self.detected_name}', qty={self.quantity}, confidence={self.confidence_score})>"

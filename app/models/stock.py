from typing import TYPE_CHECKING
from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product import Product


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    real_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reserved_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="stock", lazy="selectin")

    @hybrid_property
    def available_qty(self) -> float:
        """Computed available quantity: real_qty - reserved_qty."""
        return self.real_qty - self.reserved_qty

    @available_qty.expression
    def available_qty(cls):
        """SQL expression for available_qty to allow filtering/sorting in database queries."""
        return cls.real_qty - cls.reserved_qty

    def __repr__(self) -> str:
        return f"<Stock(id={self.id}, product_id={self.product_id}, real={self.real_qty}, reserved={self.reserved_qty}, available={self.available_qty})>"

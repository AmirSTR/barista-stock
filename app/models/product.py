from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.stock import Stock
    from app.models.order import OrderItem
    from app.models.supply import SupplyItem


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)  # 'шт.', 'кг', 'л', 'бут.'
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # 1:1 relationship with Stock
    stock: Mapped[Optional["Stock"]] = relationship(
        "Stock",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Relationships
    order_items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="product", lazy="selectin"
    )
    supply_items: Mapped[List["SupplyItem"]] = relationship(
        "SupplyItem", back_populates="product", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}', category='{self.category}')>"

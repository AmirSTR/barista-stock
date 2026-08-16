from collections import defaultdict
from typing import Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.seed_data import CATEGORIES
from app.models.product import Product
from app.schemas.catalog import (
    CatalogCategoryGroup,
    CatalogProductItem,
    CatalogResponse,
)


class CatalogService:
    @staticmethod
    async def get_grouped_catalog(db: AsyncSession) -> CatalogResponse:
        """Fetch all active products, compute stock availability & is_stop,

        and group them by 8 coffee-chain categories.
        """
        # Fetch active products with stock loaded
        query = (
            select(Product)
            .options(selectinload(Product.stock))
            .where(Product.is_active == True)
            .order_by(Product.category, Product.id)
        )
        result = await db.execute(query)
        products = result.scalars().all()

        # Group by category
        grouped_dict: Dict[str, List[CatalogProductItem]] = defaultdict(list)
        total_products = 0

        for product in products:
            if product.stock:
                avail = max(0.0, product.stock.available_qty)
            else:
                avail = 0.0

            item = CatalogProductItem(
                id=product.id,
                name=product.name,
                sku=product.sku,
                category=product.category,
                unit=product.unit,
                available_qty=avail,
                is_stop=(avail <= 0),
            )
            grouped_dict[product.category].append(item)
            total_products += 1

        # Build ordered category list (prioritizing the 8 standard categories)
        categories_list: List[CatalogCategoryGroup] = []
        ordered_cat_names = [c for c in CATEGORIES if c in grouped_dict or True]
        
        # Add any other categories that might exist
        for cat in grouped_dict:
            if cat not in ordered_cat_names:
                ordered_cat_names.append(cat)

        for cat_name in ordered_cat_names:
            items = grouped_dict.get(cat_name, [])
            categories_list.append(
                CatalogCategoryGroup(
                    category=cat_name,
                    items_count=len(items),
                    items=items,
                )
            )

        return CatalogResponse(
            total_categories=len(categories_list),
            total_products=total_products,
            categories=categories_list,
        )

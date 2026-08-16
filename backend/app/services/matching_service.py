import logging
import re
from typing import Dict, List, Optional, Tuple
from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.schemas.ocr import InvoiceItemOCR, MatchedSupplyItem

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 85.0  # 85% threshold for automatic matching


class MatchingService:
    """Fuzzy matching service mapping raw OCR item names to catalog products using RapidFuzz."""

    @classmethod
    def _normalize_text(cls, text: str) -> str:
        """Normalize quotes, brackets, and extra whitespaces for robust fuzzy token matching."""
        if not text:
            return ""
        # Remove Russian and standard quotes, brackets, and special punctuation
        cleaned = re.sub(r'[«»"\'„“”\(\)\[\]\{\}]', " ", text)
        cleaned = re.sub(r"\s+", " ", cleaned).strip().lower()
        return cleaned

    @classmethod
    def match_single_item(
        cls,
        products: List[Product],
        raw_name: str,
        quantity: float,
        unit: str = "шт",
        threshold: float = SIMILARITY_THRESHOLD,
    ) -> MatchedSupplyItem:
        """Match a single raw product name against a list of catalog products."""
        if not products or not raw_name.strip():
            return MatchedSupplyItem(
                raw_name=raw_name,
                quantity=quantity,
                unit=unit,
                product_id=None,
                product_name=None,
                confidence_score=0.0,
                is_uncertain=True,
            )

        # Mapping of choice name to Product
        name_to_product: Dict[str, Product] = {prod.name: prod for prod in products}
        choices = list(name_to_product.keys())

        # Use rapidfuzz process.extractOne with WRatio and text normalization processor
        best_match = process.extractOne(
            raw_name,
            choices,
            scorer=fuzz.WRatio,
            processor=cls._normalize_text,
        )

        if not best_match:
            return MatchedSupplyItem(
                raw_name=raw_name,
                quantity=quantity,
                unit=unit,
                product_id=None,
                product_name=None,
                confidence_score=0.0,
                is_uncertain=True,
            )

        matched_name, score, _ = best_match
        matched_prod = name_to_product[matched_name]
        confidence = float(score) / 100.0

        if score >= threshold:
            # High confidence auto-match
            return MatchedSupplyItem(
                raw_name=raw_name,
                quantity=quantity,
                unit=unit,
                product_id=matched_prod.id,
                product_name=matched_prod.name,
                confidence_score=confidence,
                is_uncertain=False,
            )
        else:
            # Low confidence uncertain match
            return MatchedSupplyItem(
                raw_name=raw_name,
                quantity=quantity,
                unit=unit,
                product_id=matched_prod.id,
                product_name=matched_prod.name,
                confidence_score=confidence,
                is_uncertain=True,
            )

    @classmethod
    def match_items(
        cls,
        products: List[Product],
        ocr_items: List[InvoiceItemOCR],
        threshold: float = SIMILARITY_THRESHOLD,
    ) -> List[MatchedSupplyItem]:
        """Match all OCR items against catalog products in memory."""
        results: List[MatchedSupplyItem] = []
        for item in ocr_items:
            matched = cls.match_single_item(
                products=products,
                raw_name=item.raw_name,
                quantity=item.quantity,
                unit=item.unit or "шт",
                threshold=threshold,
            )
            results.append(matched)
        return results

    @classmethod
    async def match_invoice_items(
        cls,
        session: AsyncSession,
        ocr_items: List[InvoiceItemOCR],
        threshold: float = SIMILARITY_THRESHOLD,
    ) -> List[MatchedSupplyItem]:
        """Fetch all active catalog products from database and match against OCR line items."""
        query = select(Product).where(Product.is_active.is_(True))
        res = await session.execute(query)
        products = list(res.scalars().all())

        return cls.match_items(products=products, ocr_items=ocr_items, threshold=threshold)

from fastapi import APIRouter, Depends

from app.api import catalog, orders
from app.api.auth import require_admin_api_key
from app.api.v1.endpoints import bars, products, stocks, supplies

api_router = APIRouter()

api_router.include_router(catalog.router, prefix="/catalog", tags=["Catalog"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
api_router.include_router(bars.router, prefix="/bars", tags=["Bars"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
api_router.include_router(
    supplies.router,
    prefix="/supplies",
    tags=["Supplies"],
    dependencies=[Depends(require_admin_api_key)],
)

from app.bot.handlers.barista import barista_router
from app.bot.handlers.stoplist import stoplist_router
from app.bot.handlers.supply import supply_router
from app.bot.handlers.warehouse import warehouse_router

__all__ = [
    "barista_router",
    "warehouse_router",
    "stoplist_router",
    "supply_router",
]

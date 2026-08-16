from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import catalog, orders
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    yield
    # Shutdown actions
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount primary API endpoints at /api/...
app.include_router(catalog.router, prefix="/api/catalog", tags=["Catalog"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])

# Mount versioned API router at /api/v1/...
app.include_router(api_router, prefix=settings.API_V1_STR)


# Health check
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "version": "0.1.0",
    }

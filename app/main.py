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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount primary API endpoints at /api/...
app.include_router(catalog.router, prefix="/api/catalog", tags=["Catalog"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])

# Mount versioned API router at /api/v1/...
app.include_router(api_router, prefix=settings.API_V1_STR)


import os
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Health check
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


# Check for pre-built frontend distribution
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
frontend_dist = os.path.join(base_dir, "frontend", "dist")

if os.path.isdir(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Serve static file if it exists in dist
        target_file = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(target_file):
            return FileResponse(target_file)
        # Fallback to index.html for SPA routing
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
        return {"status": "ok", "service": settings.PROJECT_NAME}
else:
    @app.get("/", tags=["Health"])
    async def root():
        return {
            "status": "ok",
            "service": settings.PROJECT_NAME,
            "docs_url": "/docs",
            "version": "0.1.0",
        }

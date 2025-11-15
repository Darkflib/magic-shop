"""Main FastAPI application for the Magical Emporium."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import admin, public


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events.

    Args:
        app: The FastAPI application instance

    Yields:
        Control back to FastAPI during application runtime
    """
    # Startup: Initialize the database
    init_db()
    yield
    # Shutdown: Clean up resources (none needed currently)


# Create the FastAPI application
app = FastAPI(
    title="Magical Emporium",
    description="A whimsical storefront for magical items and artifacts",
    version="1.0.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Mount images directory for serving product images
from pathlib import Path
from app.config import Config
image_dir = Config.get_image_dir()
if image_dir.exists():
    app.mount("/images", StaticFiles(directory=str(image_dir)), name="images")

# Include routers
app.include_router(public.router, tags=["Public"])
app.include_router(admin.router, tags=["Admin"])


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring.

    Returns:
        Dictionary with status information
    """
    return {"status": "healthy", "service": "magical-emporium"}

"""Main FastAPI application for the Magical Emporium."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routes import public


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

# Include routers
app.include_router(public.router, tags=["Public"])


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring.

    Returns:
        Dictionary with status information
    """
    return {"status": "healthy", "service": "magical-emporium"}

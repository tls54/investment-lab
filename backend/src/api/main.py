"""
FastAPI application for Investment Lab.

This is the entry point for the API server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import configuration
from ..core.config import settings

# Import our routers
from .routers import prices
from .routers import prices, forecasts


# Create the FastAPI application instance
app = FastAPI(
    title=settings.api_title,
    description="API for fetching asset prices and financial analysis",
    version=settings.api_version,
    debug=settings.debug
)

# CORS middleware - configured from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prices.router, prefix="/api", tags=["prices"])
app.include_router(forecasts.router, prefix="/api", tags=["forecasts"])


@app.get("/")
async def root():
    """Root endpoint - returns API status."""
    return {
        "status": "running",
        "message": settings.api_title,
        "version": settings.api_version,
        "environment": settings.environment
    }


# Health check endpoint - standard practice for production apps
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Load balancers and monitoring tools hit this to check if the app is alive.
    Returns 200 OK if everything is working.
    """
    return {"status": "healthy"}
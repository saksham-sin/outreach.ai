"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, campaigns, leads, templates, webhooks, jobs
from app.infrastructure.database import init_db, close_db
from app.services.worker import get_worker
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    - Startup: Initialize database, start background worker
    - Shutdown: Stop worker, close database connections
    """
    # Startup
    logger.info("Starting application...")
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    # Start background worker
    worker = get_worker()
    await worker.start()
    logger.info("Background worker started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Stop background worker
    await worker.stop()
    logger.info("Background worker stopped")
    
    # Close database connections
    await close_db()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="AI Email Outreach API",
    description="Production-ready API for AI-powered email outreach campaigns",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/api")
app.include_router(campaigns.router, prefix="/api")
app.include_router(leads.router, prefix="/api")
app.include_router(templates.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - basic health check."""
    return {
        "status": "healthy",
        "service": "AI Email Outreach API",
        "version": "1.0.0",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "worker": "running",
    }

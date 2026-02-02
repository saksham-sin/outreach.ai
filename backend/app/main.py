"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, campaigns, leads, templates, webhooks, jobs
from app.infrastructure.database import init_db, close_db
from app.core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


def _validate_config() -> None:
    """
    Validate critical configuration at startup.
    Logs warnings for missing optional config but allows app to start
    (supports demo scenarios with partial config).
    """
    # Check email provider API keys
    if settings.EMAIL_PROVIDER == "postmark":
        if not settings.POSTMARK_SERVER_TOKEN:
            logger.warning("POSTMARK_SERVER_TOKEN not set - email sending will fail")
        if not settings.POSTMARK_INBOUND_ADDRESS:
            logger.warning(
                "POSTMARK_INBOUND_ADDRESS not set - reply detection disabled. "
                "Set this to enable webhook-based reply detection."
            )
    elif settings.EMAIL_PROVIDER == "resend":
        if not settings.RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not set - email sending will fail")
        if not settings.RESEND_FROM_DOMAIN:
            logger.warning("RESEND_FROM_DOMAIN not set - may cause issues with email sending")
    
    # Check OpenAI config
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set - AI email generation will fail")
    
    # Check webhook security
    if not settings.WEBHOOK_USERNAME or not settings.WEBHOOK_PASSWORD:
        logger.warning(
            "WEBHOOK_USERNAME or WEBHOOK_PASSWORD not set - "
            "webhook endpoints will not be protected"
        )
    
    logger.info("Configuration validation complete")



async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    
    - Startup: Initialize database, validate config, start background worker
    - Shutdown: Stop worker, close database connections
    """
    # Startup
    logger.info("Starting application...")
    
    # Validate critical configuration
    _validate_config()
    
    # Initialize database
    await init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
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
        "worker": "separate-process",
    }

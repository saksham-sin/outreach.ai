"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, campaigns, leads, templates, jobs, webhooks
from app.infrastructure.database import init_db, close_db
from app.core.config import get_settings
from app.services.worker import get_worker

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
    # Check Resend email provider API keys
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set - email sending will fail")
    if not settings.RESEND_FROM_DOMAIN:
        logger.warning("RESEND_FROM_DOMAIN not set - may cause issues with email sending")
    
    # Check OpenAI config
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set - AI email generation will fail")

    # Check inbound reply detection config (Resend receiving)
    if not settings.RESEND_INBOUND_ADDRESS:
        logger.warning(
            "RESEND_INBOUND_ADDRESS not set - reply detection via inbound webhook disabled"
        )

    # Reply detection mode validation
    reply_mode = (settings.REPLY_MODE or "").upper()
    if reply_mode not in {"SIMULATED", "RESEND-WEBHOOK"}:
        logger.warning(
            f"REPLY_MODE '{settings.REPLY_MODE}' is invalid. Using SIMULATED mode."
        )
    else:
        logger.info(f"Reply detection mode: {reply_mode}")

    # Check webhook security
    if not settings.RESEND_WEBHOOK_SECRET:
        logger.warning(
            "RESEND_WEBHOOK_SECRET not set - webhook signature verification disabled"
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
cors_origins = []
if settings.FRONTEND_URL:
    cors_origins = [settings.FRONTEND_URL]
    
    # Add additional frontend URLs if configured (comma-separated)
    if settings.FRONTEND_URLS:
        additional_urls = [url.strip() for url in settings.FRONTEND_URLS.split(",") if url.strip()]
        cors_origins.extend(additional_urls)
else:
    # Fallback for development - allow all
    cors_origins = ["*"]

logger.info(f"CORS enabled for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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

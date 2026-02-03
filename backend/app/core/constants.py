"""Application constants - centralized configuration values."""

from enum import Enum


class EmailType(str, Enum):
    """Email type for routing sender configuration."""
    AUTH = "auth"  # Authentication emails (magic links) - no-reply
    OUTREACH = "outreach"  # Campaign and follow-up emails - hello


# Campaign Settings
MAX_CAMPAIGN_STEPS = 3
MIN_CAMPAIGN_STEPS = 1

# Email Job Retry Settings
RETRY_DELAYS_MINUTES = [1, 5, 15]  # Exponential backoff: 1min, 5min, 15min

# Lead Import
REQUIRED_CSV_COLUMNS = ["email"]
OPTIONAL_CSV_COLUMNS = ["first_name", "company"]
MAX_LEADS_PER_IMPORT = 10000

# Template Placeholders
TEMPLATE_PLACEHOLDERS = {
    "first_name": "{{first_name}}",
    "company": "{{company}}",
    "email": "{{email}}",
}

# Default delay between steps (in days)
DEFAULT_STEP_DELAYS = {
    1: 0,   # First email sent immediately
    2: 3,   # Second email after 3 days
    3: 5,   # Third email after 5 more days
}

# Magic Link
MAGIC_LINK_PATH = "/#/verify"

# Worker
WORKER_BATCH_SIZE = 100  # Max jobs to process per poll cycle

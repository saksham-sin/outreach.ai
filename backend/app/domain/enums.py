"""Domain enums for status tracking and state machines."""

from enum import Enum


class CampaignStatus(str, Enum):
    """Campaign lifecycle states."""
    
    DRAFT = "draft"           # Campaign created, not yet launched
    ACTIVE = "active"         # Campaign is running, emails being sent
    PAUSED = "paused"         # Campaign temporarily stopped
    COMPLETED = "completed"   # All leads processed, no pending jobs

    @classmethod
    def can_transition(cls, from_status: "CampaignStatus", to_status: "CampaignStatus") -> bool:
        """Check if a status transition is valid."""
        valid_transitions = {
            cls.DRAFT: {cls.ACTIVE},
            cls.ACTIVE: {cls.PAUSED, cls.COMPLETED},
            cls.PAUSED: {cls.ACTIVE, cls.COMPLETED},
            cls.COMPLETED: set(),  # Terminal state
        }
        return to_status in valid_transitions.get(from_status, set())


class LeadStatus(str, Enum):
    """Lead processing states."""
    
    PENDING = "pending"       # Lead imported, not yet contacted
    CONTACTED = "contacted"   # At least one email sent
    REPLIED = "replied"       # Lead replied (terminal - stops follow-ups)
    FAILED = "failed"         # All send attempts failed (terminal)

    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in {LeadStatus.REPLIED, LeadStatus.FAILED}


class JobStatus(str, Enum):
    """Email job execution states."""
    
    PENDING = "pending"       # Job scheduled, waiting to execute
    SENT = "sent"             # Email successfully sent
    FAILED = "failed"         # All retry attempts exhausted
    SKIPPED = "skipped"       # Job skipped (lead replied, campaign paused, etc.)


class EmailTone(str, Enum):
    """Available email tones for AI generation."""
    
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    URGENT = "urgent"
    FRIENDLY = "friendly"
    DIRECT = "direct"

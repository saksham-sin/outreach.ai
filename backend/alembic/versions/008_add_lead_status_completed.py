"""Add COMPLETED status to leadstatus enum

Revision ID: 008_add_lead_status_completed
Revises: 007_rename_message_id
Create Date: 2026-02-04 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008_add_lead_status_completed'
down_revision: Union[str, None] = '007_rename_message_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add COMPLETED status to leadstatus enum."""
    # PostgreSQL doesn't support adding values to existing enums directly
    # So we need to: 1. Create new type, 2. Cast old column to new type, 3. Drop old type, 4. Rename new type
    op.execute("""
        ALTER TYPE leadstatus ADD VALUE 'COMPLETED' BEFORE 'FAILED';
    """)


def downgrade() -> None:
    """Remove COMPLETED status from leadstatus enum - note: PostgreSQL cannot remove enum values, this is a no-op."""
    # PostgreSQL doesn't allow removing enum values once added
    # This is a one-way migration
    pass

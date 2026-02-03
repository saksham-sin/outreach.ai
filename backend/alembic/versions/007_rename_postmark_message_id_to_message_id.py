"""Rename postmark_message_id to message_id for provider neutrality

Revision ID: 007_rename_postmark_message_id_to_message_id
Revises: 006_add_profile_completed_flag
Create Date: 2026-02-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007_rename_message_id'
down_revision: Union[str, None] = '006_add_profile_completed_flag'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename postmark_message_id to message_id for provider-neutral tracking."""
    op.alter_column(
        'email_jobs',
        'postmark_message_id',
        new_column_name='message_id'
    )


def downgrade() -> None:
    """Rename message_id back to postmark_message_id."""
    op.alter_column(
        'email_jobs',
        'message_id',
        new_column_name='postmark_message_id'
    )

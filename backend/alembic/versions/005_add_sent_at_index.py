"""Add index on email_jobs.sent_at for query performance

Revision ID: 005_add_sent_at_index
Revises: 004_add_delay_minutes
Create Date: 2026-02-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005_add_sent_at_index'
down_revision: Union[str, None] = '004_add_delay_minutes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add index on sent_at for query performance
    op.create_index(
        'ix_email_jobs_sent_at',
        'email_jobs',
        ['sent_at'],
        existing_ok=True
    )


def downgrade() -> None:
    op.drop_index('ix_email_jobs_sent_at', table_name='email_jobs')


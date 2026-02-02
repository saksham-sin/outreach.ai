"""Add composite indexes for query optimization

Revision ID: 003_add_composite_indexes
Revises: 002_timezone_support
Create Date: 2026-02-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '003_add_composite_indexes'
down_revision: Union[str, None] = '7dba13c5edeb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Composite index for leads queries filtering by campaign + status
    # Optimizes: SELECT * FROM leads WHERE campaign_id = ? AND status = ?
    op.create_index(
        'ix_leads_campaign_id_status',
        'leads',
        ['campaign_id', 'status'],
        unique=False
    )
    
    # Composite index for email_jobs queries filtering by campaign + status
    # Optimizes: SELECT * FROM email_jobs WHERE campaign_id = ? AND status = ?
    op.create_index(
        'ix_email_jobs_campaign_id_status',
        'email_jobs',
        ['campaign_id', 'status'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_email_jobs_campaign_id_status', table_name='email_jobs')
    op.drop_index('ix_leads_campaign_id_status', table_name='leads')

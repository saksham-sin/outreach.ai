"""Add delay_minutes to email templates

Revision ID: 004_add_delay_minutes
Revises: 003_add_composite_indexes
Create Date: 2026-02-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '004_add_delay_minutes'
down_revision: Union[str, None] = '003_add_composite_indexes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'email_templates',
        sa.Column('delay_minutes', sa.Integer(), nullable=False, server_default='0')
    )

    # Backfill delay_minutes from existing delay_days
    op.execute("UPDATE email_templates SET delay_minutes = delay_days * 1440")

    # Remove server default after backfill
    op.alter_column('email_templates', 'delay_minutes', server_default=None)


def downgrade() -> None:
    op.drop_column('email_templates', 'delay_minutes')

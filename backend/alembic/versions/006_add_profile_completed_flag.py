"""Add profile_completed flag to users table.

Revision ID: 006_add_profile_completed_flag
Revises: 7dba13c5edeb
Create Date: 2026-02-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_add_profile_completed_flag'
down_revision = '7dba13c5edeb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add profile_completed column to users table
    op.add_column('users', sa.Column('profile_completed', sa.Boolean(), nullable=False, server_default='false'))
    # Create index on profile_completed for filtering
    op.create_index(op.f('ix_users_profile_completed'), 'users', ['profile_completed'], unique=False)


def downgrade() -> None:
    # Remove the index
    op.drop_index(op.f('ix_users_profile_completed'), table_name='users')
    # Remove the column
    op.drop_column('users', 'profile_completed')

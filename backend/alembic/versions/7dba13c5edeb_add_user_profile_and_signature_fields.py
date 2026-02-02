"""add user profile and signature fields

Revision ID: 7dba13c5edeb
Revises: 005_add_sent_at_index
Create Date: 2026-02-02 01:49:53.332339

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '7dba13c5edeb'
down_revision: Union[str, None] = '005_add_sent_at_index'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the database connection to check for existing columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Only add columns if they don't already exist
    if 'first_name' not in columns:
        op.add_column('users', sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True))
    if 'last_name' not in columns:
        op.add_column('users', sa.Column('last_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True))
    if 'company_name' not in columns:
        op.add_column('users', sa.Column('company_name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True))
    if 'job_title' not in columns:
        op.add_column('users', sa.Column('job_title', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True))
    if 'email_signature' not in columns:
        op.add_column('users', sa.Column('email_signature', sa.Text(), nullable=True))
    if 'updated_at' not in columns:
        op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))


def downgrade() -> None:
    # Get the database connection to check for existing columns
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Only drop columns if they exist
    if 'updated_at' in columns:
        op.drop_column('users', 'updated_at')
    if 'email_signature' in columns:
        op.drop_column('users', 'email_signature')
    if 'job_title' in columns:
        op.drop_column('users', 'job_title')
    if 'company_name' in columns:
        op.drop_column('users', 'company_name')
    if 'last_name' in columns:
        op.drop_column('users', 'last_name')
    if 'first_name' in columns:
        op.drop_column('users', 'first_name')

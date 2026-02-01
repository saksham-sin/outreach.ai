"""Initial migration - create all tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create campaigns table
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('pitch', sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=False),
        sa.Column('tone', sa.Enum('PROFESSIONAL', 'CASUAL', 'URGENT', 'FRIENDLY', 'DIRECT', name='emailtone'), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', name='campaignstatus'), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campaigns_user_id'), 'campaigns', ['user_id'], unique=False)
    op.create_index(op.f('ix_campaigns_status'), 'campaigns', ['status'], unique=False)

    # Create leads table
    op.create_table(
        'leads',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('campaign_id', sa.Uuid(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('first_name', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('company', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'CONTACTED', 'REPLIED', 'FAILED', name='leadstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_leads_campaign_id'), 'leads', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_leads_email'), 'leads', ['email'], unique=False)
    op.create_index(op.f('ix_leads_status'), 'leads', ['status'], unique=False)

    # Create email_templates table
    op.create_table(
        'email_templates',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('campaign_id', sa.Uuid(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('subject', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column('body', sqlmodel.sql.sqltypes.AutoString(length=10000), nullable=False),
        sa.Column('delay_days', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_templates_campaign_id'), 'email_templates', ['campaign_id'], unique=False)

    # Create email_jobs table
    op.create_table(
        'email_jobs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('campaign_id', sa.Uuid(), nullable=False),
        sa.Column('lead_id', sa.Uuid(), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'FAILED', 'SKIPPED', name='jobstatus'), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False),
        sa.Column('last_error', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('postmark_message_id', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_jobs_campaign_id'), 'email_jobs', ['campaign_id'], unique=False)
    op.create_index(op.f('ix_email_jobs_lead_id'), 'email_jobs', ['lead_id'], unique=False)
    op.create_index(op.f('ix_email_jobs_status'), 'email_jobs', ['status'], unique=False)
    op.create_index(op.f('ix_email_jobs_scheduled_at'), 'email_jobs', ['scheduled_at'], unique=False)
    # Composite index for worker queries
    op.create_index(
        'ix_email_jobs_status_scheduled_at',
        'email_jobs',
        ['status', 'scheduled_at'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_email_jobs_status_scheduled_at', table_name='email_jobs')
    op.drop_index(op.f('ix_email_jobs_scheduled_at'), table_name='email_jobs')
    op.drop_index(op.f('ix_email_jobs_status'), table_name='email_jobs')
    op.drop_index(op.f('ix_email_jobs_lead_id'), table_name='email_jobs')
    op.drop_index(op.f('ix_email_jobs_campaign_id'), table_name='email_jobs')
    
    op.drop_index(op.f('ix_email_templates_campaign_id'), table_name='email_templates')
    
    op.drop_index(op.f('ix_leads_status'), table_name='leads')
    op.drop_index(op.f('ix_leads_email'), table_name='leads')
    op.drop_index(op.f('ix_leads_campaign_id'), table_name='leads')
    
    op.drop_index(op.f('ix_campaigns_status'), table_name='campaigns')
    op.drop_index(op.f('ix_campaigns_user_id'), table_name='campaigns')
    
    op.drop_index(op.f('ix_users_email'), table_name='users')
    
    # Drop tables
    op.drop_table('email_jobs')
    op.drop_table('email_templates')
    op.drop_table('leads')
    op.drop_table('campaigns')
    op.drop_table('users')
    
    # Drop enums
    sa.Enum(name='jobstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='leadstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='campaignstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='emailtone').drop(op.get_bind(), checkfirst=True)

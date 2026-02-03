"""Add cascade delete for all foreign keys

Revision ID: 010_cascade_delete_all_fks
Revises: 009_cascade_delete_tags
Create Date: 2026-02-04

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '010_cascade_delete_all_fks'
down_revision = '009_cascade_delete_tags'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add CASCADE to all foreign key constraints."""
    
    # leads.campaign_id -> campaigns.id
    op.drop_constraint('leads_campaign_id_fkey', 'leads', type_='foreignkey')
    op.create_foreign_key(
        'leads_campaign_id_fkey',
        'leads',
        'campaigns',
        ['campaign_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # email_templates.campaign_id -> campaigns.id
    op.drop_constraint('email_templates_campaign_id_fkey', 'email_templates', type_='foreignkey')
    op.create_foreign_key(
        'email_templates_campaign_id_fkey',
        'email_templates',
        'campaigns',
        ['campaign_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # email_jobs.campaign_id -> campaigns.id
    op.drop_constraint('email_jobs_campaign_id_fkey', 'email_jobs', type_='foreignkey')
    op.create_foreign_key(
        'email_jobs_campaign_id_fkey',
        'email_jobs',
        'campaigns',
        ['campaign_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # email_jobs.lead_id -> leads.id
    op.drop_constraint('email_jobs_lead_id_fkey', 'email_jobs', type_='foreignkey')
    op.create_foreign_key(
        'email_jobs_lead_id_fkey',
        'email_jobs',
        'leads',
        ['lead_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove CASCADE from foreign key constraints."""
    
    # email_jobs.lead_id -> leads.id
    op.drop_constraint('email_jobs_lead_id_fkey', 'email_jobs', type_='foreignkey')
    op.create_foreign_key(
        'email_jobs_lead_id_fkey',
        'email_jobs',
        'leads',
        ['lead_id'],
        ['id']
    )
    
    # email_jobs.campaign_id -> campaigns.id
    op.drop_constraint('email_jobs_campaign_id_fkey', 'email_jobs', type_='foreignkey')
    op.create_foreign_key(
        'email_jobs_campaign_id_fkey',
        'email_jobs',
        'campaigns',
        ['campaign_id'],
        ['id']
    )
    
    # email_templates.campaign_id -> campaigns.id
    op.drop_constraint('email_templates_campaign_id_fkey', 'email_templates', type_='foreignkey')
    op.create_foreign_key(
        'email_templates_campaign_id_fkey',
        'email_templates',
        'campaigns',
        ['campaign_id'],
        ['id']
    )
    
    # leads.campaign_id -> campaigns.id
    op.drop_constraint('leads_campaign_id_fkey', 'leads', type_='foreignkey')
    op.create_foreign_key(
        'leads_campaign_id_fkey',
        'leads',
        'campaigns',
        ['campaign_id'],
        ['id']
    )

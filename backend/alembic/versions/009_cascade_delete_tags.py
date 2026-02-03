"""Add cascade delete for campaign tags

Revision ID: 009_cascade_delete_tags
Revises: 008_add_lead_status_completed
Create Date: 2026-02-04

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '009_cascade_delete_tags'
down_revision = '008_add_lead_status_completed'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add CASCADE to campaign_tags foreign key."""
    # Drop existing foreign key constraint
    op.drop_constraint('campaign_tags_campaign_id_fkey', 'campaign_tags', type_='foreignkey')
    
    # Re-add with CASCADE
    op.create_foreign_key(
        'campaign_tags_campaign_id_fkey',
        'campaign_tags',
        'campaigns',
        ['campaign_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Remove CASCADE from campaign_tags foreign key."""
    # Drop CASCADE foreign key
    op.drop_constraint('campaign_tags_campaign_id_fkey', 'campaign_tags', type_='foreignkey')
    
    # Re-add without CASCADE
    op.create_foreign_key(
        'campaign_tags_campaign_id_fkey',
        'campaign_tags',
        'campaigns',
        ['campaign_id'],
        ['id']
    )

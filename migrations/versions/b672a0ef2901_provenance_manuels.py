"""Langue et provenance des manuels officiels.

Revision ID: b672a0ef2901
Revises: a520bf771e03
"""
from alembic import op
import sqlalchemy as sa

revision = 'b672a0ef2901'
down_revision = 'a520bf771e03'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('manuel_passages') as batch:
        batch.add_column(sa.Column('document_metadata', sa.JSON(), nullable=False, server_default='{}'))

def downgrade():
    with op.batch_alter_table('manuel_passages') as batch:
        batch.drop_column('document_metadata')

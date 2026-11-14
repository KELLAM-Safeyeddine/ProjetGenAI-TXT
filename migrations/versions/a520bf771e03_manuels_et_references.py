"""Manuels indexés et références persistantes des messages.

Revision ID: a520bf771e03
Revises: cf8f8477861d
"""

import sqlalchemy as sa
from alembic import op

revision = 'a520bf771e03'
down_revision = 'cf8f8477861d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'manuel_passages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('brand', sa.String(80), nullable=False),
        sa.Column('model', sa.String(80), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('page', sa.Integer(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('section', sa.String(200), nullable=False),
        sa.Column('contenu', sa.Text(), nullable=False),
        sa.Column('search_index', sa.Text(), nullable=False),
        sa.Column('source', sa.String(1000), nullable=False),
        sa.Column('added_at', sa.String(10), nullable=False),
        sa.UniqueConstraint('brand', 'model', 'year', 'page', 'position', name='uq_manuel_passage'),
    )
    op.create_index('ix_manuel_vehicle', 'manuel_passages', ['brand', 'model', 'year'])
    with op.batch_alter_table('messages') as batch:
        batch.add_column(sa.Column('source', sa.String(24)))
        batch.add_column(sa.Column('references', sa.JSON(), nullable=False, server_default='[]'))
        batch.add_column(sa.Column('vehicle_context', sa.JSON()))


def downgrade():
    with op.batch_alter_table('messages') as batch:
        batch.drop_column('vehicle_context')
        batch.drop_column('references')
        batch.drop_column('source')
    op.drop_index('ix_manuel_vehicle', table_name='manuel_passages')
    op.drop_table('manuel_passages')

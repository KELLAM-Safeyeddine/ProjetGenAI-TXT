"""Passages web locaux et ligne de source persistante."""

import sqlalchemy as sa
from alembic import op

revision = 'd3164bd2b7a1'
down_revision = 'c904dfba8620'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('messages', sa.Column('source_line', sa.Text(), nullable=True))
    op.create_table(
        'web_passages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('url', sa.String(1500), nullable=False),
        sa.Column('site_name', sa.String(100), nullable=False),
        sa.Column('title', sa.String(300), nullable=False),
        sa.Column('consulted_at', sa.String(25), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('region', sa.String(30), nullable=False),
        sa.Column('kind', sa.String(30), nullable=False),
        sa.UniqueConstraint('url', 'position', name='uq_web_passage'),
    )


def downgrade():
    op.drop_table('web_passages')
    with op.batch_alter_table('messages') as batch:
        batch.drop_column('source_line')

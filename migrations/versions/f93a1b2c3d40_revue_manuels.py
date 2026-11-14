"""Revue administrateur et journal indépendant des réimports."""

import sqlalchemy as sa
from alembic import op

revision = 'f93a1b2c3d40'
down_revision = 'f82b650ca410'
branch_labels = depends_on = None


def upgrade():
    with op.batch_alter_table('manuel_passages') as batch:
        batch.add_column(
            sa.Column('review_revision', sa.Integer(), nullable=False, server_default='0')
        )
    op.create_table(
        'manual_reviews',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('admin_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('passage_id', sa.Integer(), nullable=False),
        sa.Column('identity', sa.JSON(), nullable=False),
        sa.Column('before', sa.JSON(), nullable=False),
        sa.Column('after', sa.JSON(), nullable=False),
        sa.Column('action', sa.String(16), nullable=False),
        sa.Column('note', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table('manual_reviews')
    with op.batch_alter_table('manuel_passages') as batch:
        batch.drop_column('review_revision')

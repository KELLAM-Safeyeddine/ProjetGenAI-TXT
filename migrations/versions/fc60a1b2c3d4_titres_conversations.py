import sqlalchemy as sa
from alembic import op

revision = 'fc60a1b2c3d4'
down_revision = 'fb50a1b2c3d4'
branch_labels = depends_on = None


def upgrade():
    with op.batch_alter_table('conversations') as batch:
        batch.add_column(sa.Column('title', sa.String(80)))


def downgrade():
    with op.batch_alter_table('conversations') as batch:
        batch.drop_column('title')

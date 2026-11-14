"""Sources et synchronisation non destructive de la FAQ enrichie."""
from alembic import op
import sqlalchemy as sa
revision='c904dfba8620'
down_revision='b672a0ef2901'
branch_labels=None
depends_on=None

def upgrade():
    with op.batch_alter_table('faq') as batch:
        batch.add_column(sa.Column('slug',sa.String(100),nullable=True))
        batch.add_column(sa.Column('source',sa.String(1000),nullable=True))
        batch.add_column(sa.Column('seed_hash',sa.String(64),nullable=True))
        batch.create_unique_constraint('uq_faq_slug',['slug'])

def downgrade():
    with op.batch_alter_table('faq') as batch:
        batch.drop_constraint('uq_faq_slug',type_='unique')
        batch.drop_column('seed_hash');batch.drop_column('source');batch.drop_column('slug')

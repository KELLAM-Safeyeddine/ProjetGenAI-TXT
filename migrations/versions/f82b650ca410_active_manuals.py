"""Archive les anciens passages avant une extraction validée."""

import sqlalchemy as sa
from alembic import op

revision = 'f82b650ca410'
down_revision = 'e41ac907d256'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('manuel_passages') as batch:
        batch.add_column(
            sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.false())
        )
    connection = op.get_bind()
    vehicles = sa.table('vehicles', sa.column('manual_reference', sa.JSON()))
    connection.execute(vehicles.update().values(manual_reference=None))
    with op.batch_alter_table('manuel_passages') as batch:
        batch.alter_column('active', existing_type=sa.Boolean(), server_default=sa.true())


def downgrade():
    with op.batch_alter_table('manuel_passages') as batch:
        batch.drop_column('active')

"""Révocation des sessions après changement de mot de passe."""

import sqlalchemy as sa
from alembic import op

revision = 'fa401c2d3e50'
down_revision = 'f93a1b2c3d40'
branch_labels = depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch:
        batch.add_column(
            sa.Column('auth_version', sa.Integer(), nullable=False, server_default='1')
        )


def downgrade():
    with op.batch_alter_table('users') as batch:
        batch.drop_column('auth_version')

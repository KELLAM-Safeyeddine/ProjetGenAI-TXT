import sqlalchemy as sa
from alembic import op

revision = 'fb50a1b2c3d4'
down_revision = 'fa401c2d3e50'
branch_labels = depends_on = None


def upgrade():
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'message_id', sa.Integer(), sa.ForeignKey('messages.id'), nullable=False, unique=True
        ),
        sa.Column(
            'user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False
        ),
        sa.Column('helpful', sa.Boolean(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_feedback_user_id', 'feedback', ['user_id'])


def downgrade():
    op.drop_table('feedback')

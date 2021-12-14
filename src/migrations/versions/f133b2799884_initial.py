"""initial

Revision ID: f133b2799884
Revises: 
Create Date: 2021-12-12 21:24:55.603240

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f133b2799884'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'events',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('timestamp', sa.Integer, nullable=False)
    )
    op.create_table(
        'albums',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('timestamp', sa.Integer, nullable=False),
        sa.Column('event_id', sa.String(36), nullable=False)
    )


def downgrade():
    op.drop_table('events')
    op.drop_table('albums')

"""hidden_albums

Revision ID: 38dad941e998
Revises: f133b2799884
Create Date: 2022-01-06 19:55:49.799193

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '38dad941e998'
down_revision = 'f133b2799884'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name='albums',
        column=sa.Column('hidden_secret', sa.String(36), nullable=True, default=None)
    )


def downgrade():
    op.drop_column('albums', 'hidden_secret')

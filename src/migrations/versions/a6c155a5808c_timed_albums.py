"""timed_albums

Revision ID: a6c155a5808c
Revises: 38dad941e998
Create Date: 2022-01-06 20:49:48.362478

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a6c155a5808c'
down_revision = '38dad941e998'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name='albums',
        column=sa.Column('release_time', sa.DateTime, nullable=True, default=None)
    )


def downgrade():
    op.drop_column('albums', 'release_time')

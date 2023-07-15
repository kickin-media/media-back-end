"""Add GPS to photos.

Revision ID: 0a178d5f6a42
Revises: 81b987950142
Create Date: 2023-07-15 16:29:18.325966

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0a178d5f6a42'
down_revision = '81b987950142'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name='photos',
        column=sa.Column('gps_lat', sa.Float, nullable=True, default=None)
    )
    op.add_column(
        table_name='photos',
        column=sa.Column('gps_lon', sa.Float, nullable=True, default=None)
    )


def downgrade():
    op.drop_column('photos', 'gps_lat')
    op.drop_column('photos', 'gps_lon')

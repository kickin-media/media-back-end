"""uploads_exif_update_id

Revision ID: 49c8b1410e77
Revises: fefd96909330
Create Date: 2022-05-19 21:02:52.344928

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '49c8b1410e77'
down_revision = 'fefd96909330'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name='photos',
        column=sa.Column('exif_update_secret', sa.String(36), nullable=True, default=None)
    )


def downgrade():
    op.drop_column('photos', 'exif_update_secret')

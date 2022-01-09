"""album_cover

Revision ID: fefd96909330
Revises: a6c155a5808c
Create Date: 2022-01-09 14:29:45.494898

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fefd96909330'
down_revision = 'a6c155a5808c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name='albums',
        column=sa.Column('cover_id', sa.String(36), sa.ForeignKey('photos.id'), nullable=True, default=None)
    )


def downgrade():
    op.drop_column('albums', 'cover_id')

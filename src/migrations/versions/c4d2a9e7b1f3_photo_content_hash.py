"""Add content hash to photos.

Revision ID: c4d2a9e7b1f3
Revises: b3e7d9f1c4a8
Create Date: 2026-10-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c4d2a9e7b1f3'
down_revision = 'b3e7d9f1c4a8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name='photos',
        column=sa.Column('content_hash', sa.String(64), nullable=True, default=None)
    )
    op.create_index('ix_photos_content_hash', 'photos', ['content_hash'])


def downgrade():
    op.drop_index('ix_photos_content_hash', table_name='photos')
    op.drop_column('photos', 'content_hash')

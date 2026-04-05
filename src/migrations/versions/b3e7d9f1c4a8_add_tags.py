"""Add tags.

Revision ID: b3e7d9f1c4a8
Revises: 0a178d5f6a42
Create Date: 2026-04-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3e7d9f1c4a8'
down_revision = '0a178d5f6a42'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'tags',
        sa.Column('tag_slug', sa.String(100), primary_key=True),
        sa.Column('tag_description', sa.Text, nullable=False),
        sa.Column('supports_value', sa.Boolean, nullable=False),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_general_ci',
    )

    op.create_table(
        'tags_photos',
        sa.Column('tag_slug', sa.String(100), sa.ForeignKey('tags.tag_slug'), primary_key=True, index=True),
        sa.Column('photo_id', sa.String(36), sa.ForeignKey('photos.id'), primary_key=True, index=True),
        sa.Column('tag_value', sa.String(255), nullable=False, server_default='', primary_key=True),
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_general_ci',
    )


def downgrade():
    op.drop_table('tags_photos')
    op.drop_table('tags')

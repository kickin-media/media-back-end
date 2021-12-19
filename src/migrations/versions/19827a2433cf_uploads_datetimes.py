"""uploads_datetimes

Revision ID: 19827a2433cf
Revises: f133b2799884
Create Date: 2021-12-19 20:31:07.273119

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '19827a2433cf'
down_revision = 'f133b2799884'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'uploads',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('expires', sa.DateTime, nullable=False),
        sa.Column('presigned_url', sa.Text, nullable=False)
    )
    op.create_table(
        'photos',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('location', sa.String(100), nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('exif_data', sa.Text, nullable=True),
        sa.Column('creator', sa.String(50), nullable=False),
        sa.Column('creator_name', sa.String(100), nullable=False)
    )
    op.create_table(
        'albums_photos',
        sa.Column('album_id', sa.String(36), primary_key=True, index=True),
        sa.Column('photo_id', sa.String(36), primary_key=True, index=True)
    )
    op.alter_column(
        'events',
        'timestamp',
        type_=sa.DateTime
    )
    op.alter_column(
        'albums',
        'timestamp',
        type_=sa.DateTime
    )


def downgrade():
    op.drop_table('uploads')
    op.drop_table('photos')
    op.drop_table('albums_photos')
    op.alter_column(
        'events',
        'timestamp',
        type_=sa.Integer
    )
    op.alter_column(
        'albums',
        'timestamp',
        type_=sa.Integer
    )

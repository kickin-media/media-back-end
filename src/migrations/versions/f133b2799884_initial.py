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
        sa.Column('timestamp', sa.DateTime, nullable=False)
    )
    op.create_table(
        'albums',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('event_id', sa.String(36), sa.ForeignKey('events.id'), nullable=False)
    )
    op.create_table(
        'authors',
        sa.Column('id', sa.String(100), primary_key=True, index=True),
        sa.Column('name', sa.String(100))
    )
    op.create_table(
        'photos',
        sa.Column('id', sa.String(36), primary_key=True, index=True),
        sa.Column('secret', sa.String(36)),
        sa.Column('timestamp', sa.DateTime, nullable=True, index=True),
        sa.Column('author_id', sa.String(50), sa.ForeignKey('authors.id'), nullable=False, index=True),
        sa.Column('exif_data', sa.Text, nullable=True),
        sa.Column('uploaded_at', sa.DateTime, nullable=False),
        sa.Column('upload_processed', sa.Boolean, nullable=False)
    )
    op.create_table(
        'albums_photos',
        sa.Column('album_id', sa.String(36), sa.ForeignKey('albums.id'), primary_key=True, index=True),
        sa.Column('photo_id', sa.String(36), sa.ForeignKey('photos.id'), primary_key=True, index=True)
    )


def downgrade():
    op.drop_table('events')
    op.drop_table('albums')
    op.drop_table('photos')
    op.drop_table('albums_photos')
    op.drop_table('authors')

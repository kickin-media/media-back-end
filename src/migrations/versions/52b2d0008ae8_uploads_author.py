"""uploads_author

Revision ID: 52b2d0008ae8
Revises: 19827a2433cf
Create Date: 2021-12-19 20:47:44.487438

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '52b2d0008ae8'
down_revision = '19827a2433cf'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'uploads',
        sa.Column('author', sa.String(50), nullable=False),
    )


def downgrade():
    op.drop_column(
        'uploads',
        'author'
    )

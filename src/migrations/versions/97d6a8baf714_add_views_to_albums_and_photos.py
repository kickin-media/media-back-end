"""add views to albums and photos

Revision ID: 97d6a8baf714
Revises: 49c8b1410e77
Create Date: 2022-12-10 14:06:04.898268

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97d6a8baf714'
down_revision = '49c8b1410e77'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name='photos',
        column=sa.Column('views', sa.BigInteger, nullable=False, default=0)
    )
    op.add_column(
        table_name='albums',
        column=sa.Column('views', sa.BigInteger, nullable=False, default=0)
    )


def downgrade():
    op.drop_column('photos', 'views')
    op.drop_column('albums', 'views')
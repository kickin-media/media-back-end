"""lock events

Revision ID: 81b987950142
Revises: 97d6a8baf714
Create Date: 2022-12-10 15:53:21.167896

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '81b987950142'
down_revision = '97d6a8baf714'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        table_name='events',
        column=sa.Column('locked', sa.Boolean, nullable=False, default=False)
    )


def downgrade():
    op.drop_column('events', 'locked')

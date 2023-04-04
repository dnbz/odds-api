"""add_unaccent_extension

Revision ID: 6edae228189e
Revises: ab67a86ccd33
Create Date: 2023-04-02 03:44:29.706648

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6edae228189e'
down_revision = 'ab67a86ccd33'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS unaccent;')


def downgrade() -> None:
    op.execute('DROP EXTENSION IF EXISTS unaccent;')

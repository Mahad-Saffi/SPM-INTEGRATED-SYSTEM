"""Add lab_id column to projects table

Revision ID: 003
Revises: 2a5b422edea0
Create Date: 2025-12-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '2a5b422edea0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add lab_id column to projects table
    op.add_column('projects', sa.Column('lab_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove lab_id column from projects table
    op.drop_column('projects', 'lab_id')

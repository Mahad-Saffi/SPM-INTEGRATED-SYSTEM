"""Add Epic and Story models

Revision ID: 001
Revises: 
Create Date: 2025-11-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create epics table
    op.create_table('epics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create stories table
    op.create_table('stories',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('epic_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['epic_id'], ['epics.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Update tasks table to add story_id foreign key and order column
    op.add_column('tasks', sa.Column('story_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('tasks', sa.Column('order', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_tasks_story_id', 'tasks', 'stories', ['story_id'], ['id'])
    
    # Remove old epic_id and story_id VARCHAR columns if they exist
    try:
        op.drop_column('tasks', 'epic_id')
    except:
        pass


def downgrade() -> None:
    op.drop_constraint('fk_tasks_story_id', 'tasks', type_='foreignkey')
    op.drop_column('tasks', 'story_id')
    op.drop_column('tasks', 'order')
    op.drop_table('stories')
    op.drop_table('epics')

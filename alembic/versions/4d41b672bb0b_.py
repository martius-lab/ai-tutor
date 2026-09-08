"""empty message

Revision ID: 4d41b672bb0b
Revises: bf1716aeb859
Create Date: 2025-12-03 12:53:44.934594

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

from aitutor.config import get_default_prompts

# revision identifiers, used by Alembic.
revision: str = '4d41b672bb0b'
down_revision: Union[str, None] = 'bf1716aeb859'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # 1. Create the new prompt table
    op.create_table('prompt',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('prompt_template', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', name='uq_prompt_name')
    )

    # 2. Data Migration: Populate prompt table from config
    # We define a temporary table helper to insert data using core SQLAlchemy
    prompt_table = sa.table(
        'prompt',
        sa.column('name', sa.String),
        sa.column('prompt_template', sa.String)
    )

    # Load configuration
    prompts_data = get_default_prompts()
    if prompts_data:
        op.bulk_insert(prompt_table, prompts_data)

    # 3. Add the prompt_id column (nullable at first)
    with op.batch_alter_table('exercise', schema=None) as batch_op:
        batch_op.add_column(sa.Column('prompt_id', sa.Integer(), nullable=True))

    # 4. Set exercise prompts.  THIS IS A LOSSY OPERATION!  Simply use the first prompt
    # for all exercises.
    op.execute("""
        UPDATE exercise
        SET prompt_id = (SELECT id FROM prompt ORDER BY id LIMIT 1)
    """)

    # 5. Add Foreign Key and drop old columns
    with op.batch_alter_table('exercise', schema=None) as batch_op:
        batch_op.create_foreign_key('fk_exercise_prompt_id', 'prompt', ['prompt_id'], ['id'])
        batch_op.drop_column('prompt')
        batch_op.drop_column('prompt_name')


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('exercise', schema=None) as batch_op:
        # Restore old columns
        batch_op.add_column(sa.Column('prompt_name', sa.VARCHAR(), server_default=sa.text("('')"), nullable=False))
        batch_op.add_column(sa.Column('prompt', sa.VARCHAR(), nullable=False))
        batch_op.drop_constraint('fk_exercise_prompt_id', type_='foreignkey')

    # Attempt to restore data (reverse logic)
    op.execute("""
        UPDATE exercise
        SET prompt_name = (SELECT name FROM prompt WHERE prompt.id = exercise.prompt_id),
            prompt = (SELECT prompt_template FROM prompt WHERE prompt.id = exercise.prompt_id)
        WHERE prompt_id IS NOT NULL
    """)

    with op.batch_alter_table('exercise', schema=None) as batch_op:
        batch_op.drop_column('prompt_id')

    op.drop_table('prompt')

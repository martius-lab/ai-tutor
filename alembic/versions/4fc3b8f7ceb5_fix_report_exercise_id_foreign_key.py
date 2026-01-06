"""Fix report exercise_id foreign key

Revision ID: 4fc3b8f7ceb5
Revises: 8851001f41b5
Create Date: 2026-01-06 19:34:55.840984

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '4fc3b8f7ceb5'
down_revision: Union[str, None] = '8851001f41b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # For SQLite, we need to recreate the table to change the foreign key constraint
    # Batch mode with naming_convention will help SQLite name the constraints
    with op.batch_alter_table(
        'report',
        schema=None,
        naming_convention={
            "fk": "fk_%(table_name)s_%(column_0_name)s",
        }
    ) as batch_op:
        # Make exercise_id nullable
        batch_op.alter_column('exercise_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        # Drop and recreate the foreign key
        batch_op.drop_constraint('fk_report_exercise_id', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_report_exercise_id',
            'exercise',
            ['exercise_id'],
            ['id'],
            ondelete='SET NULL'
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert to the old schema
    with op.batch_alter_table(
        'report',
        schema=None,
        naming_convention={
            "fk": "fk_%(table_name)s_%(column_0_name)s",
        }
    ) as batch_op:
        batch_op.drop_constraint('fk_report_exercise_id', type_='foreignkey')
        batch_op.create_foreign_key(
            'fk_report_exercise_id',
            'exercise',
            ['exercise_id'],
            ['id'],
            ondelete='CASCADE'
        )
        batch_op.alter_column('exercise_id',
               existing_type=sa.INTEGER(),
               nullable=False)

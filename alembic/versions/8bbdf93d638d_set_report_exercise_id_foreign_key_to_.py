"""Set report exercise_id foreign key to SET NULL on delete

Revision ID: 8bbdf93d638d
Revises: 984c654a75a6
Create Date: 2026-01-10 17:14:04.381938

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '8bbdf93d638d'
down_revision: Union[str, None] = '984c654a75a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Manually edited: For SQLite, batch mode with naming_convention will
    # recreate the table with the correct foreign key constraint
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
        # Drop and recreate the foreign key with SET NULL
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
    # Revert to the old schema with CASCADE
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

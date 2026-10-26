"""Add per-exercise analysis preference and remove obsolete core-point requirement.

Revision ID: f802b1b017d6
Revises: fd654871fd97

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f802b1b017d6'
down_revision: Union[str, None] = 'fd654871fd97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add analysis preference, defaulting existing results to enabled."""
    with op.batch_alter_table('betacorepoint', schema=None) as batch_op:
        batch_op.drop_column('required')

    with op.batch_alter_table('betaexerciseresult', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'analysis_allowed', sa.Boolean(),
                server_default=sa.sql.true(), nullable=False,
            )
        )


def downgrade() -> None:
    """Restore the previous schema."""
    with op.batch_alter_table('betaexerciseresult', schema=None) as batch_op:
        batch_op.drop_column('analysis_allowed')

    with op.batch_alter_table('betacorepoint', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('required', sa.Boolean(), server_default=sa.sql.true(), nullable=False)
        )
"""Rename UserRole.TEACHER -> TUTOR

Revision ID: 13978d7d4420
Revises: 69ed9eeebd33
Create Date: 2025-10-08 15:30:54.000904

"""
from typing import Sequence, Union

from alembic import op
# import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '13978d7d4420'
down_revision: Union[str, None] = '69ed9eeebd33'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Based on https://stackoverflow.com/a/53639506/2095383
    # and https://stackoverflow.com/a/54357043/2095383
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        # Skip this for SQLite, which doesn't have a custom type for this
        op.execute("ALTER TYPE userrole ADD VALUE 'TUTOR'")
        op.execute("COMMIT")
    op.execute("UPDATE userinfo SET role = 'TUTOR' WHERE role = 'TEACHER'")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE userrole SET role = 'TEACHER' WHERE role = 'TUTOR'")
    # Note: Apparently PostgreSQL does not support removing enum values, so we just
    # leave the TUTOR value there but don't use it anymore...

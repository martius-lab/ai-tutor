"""Convert exercise deadlines to correct timezone.

Revision ID: 8399f8f83118
Revises: 3718ff7e3e07
Create Date: 2026-11-25 15:13:12.287456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from aitutor.global_vars import TIME_ZONE


# revision identifiers, used by Alembic.
revision: str = '8399f8f83118'
down_revision: Union[str, None] = '3718ff7e3e07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Deadlines were written as naive datetimes holding TIME_ZONE wall-clock time.  The
# column is `timestamptz` in PostgreSQL, which interpreted them in the session time zone
# (UTC).  SQLite stores the naive value as-is, so only PostgreSQL needs fixing.


def upgrade() -> None:
    """Upgrade schema."""
    if op.get_bind().engine.name != 'postgresql':
        return
    # Reinterpret the stored UTC wall-clock time as TIME_ZONE wall-clock time.
    op.execute(
        sa.text(
            "UPDATE exercise"
            " SET deadline = (deadline AT TIME ZONE 'UTC') AT TIME ZONE :tz"
            " WHERE deadline IS NOT NULL"
        ).bindparams(tz=TIME_ZONE)
    )


def downgrade() -> None:
    """Downgrade schema."""
    if op.get_bind().engine.name != 'postgresql':
        return
    op.execute(
        sa.text(
            "UPDATE exercise"
            " SET deadline = (deadline AT TIME ZONE :tz) AT TIME ZONE 'UTC'"
            " WHERE deadline IS NOT NULL"
        ).bindparams(tz=TIME_ZONE)
    )

"""merge Beta AI migration history

Revision ID: 6b9674012543
Revises: 0ce810c7ed80, 38ab9eec608b
Create Date: 2026-09-10 14:02:20.794278

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "6b9674012543"
down_revision: Union[str, None] = ("0ce810c7ed80", "38ab9eec608b")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""merge branched history

Revision ID: 0ce810c7ed80
Revises: 88396a0d3bb1, c08f4cb20e72
Create Date: 2026-09-01 15:13:31.491441

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ce810c7ed80'
down_revision: Union[str, None] = ('88396a0d3bb1', 'c08f4cb20e72')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

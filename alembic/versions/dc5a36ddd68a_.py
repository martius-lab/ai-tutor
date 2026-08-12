"""Merge alembic history heads

We somehow ended up with a branched alembic history.  This file is the result of calling
`alembic merge heads` to fix that (hence nothing in the upgrade/downgrade functions).

Revision ID: dc5a36ddd68a
Revises: 4e51f030b911, b54bd38711ed
Create Date: 2026-08-12 14:18:26.633193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc5a36ddd68a'
down_revision: Union[str, None] = ('4e51f030b911', 'b54bd38711ed')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

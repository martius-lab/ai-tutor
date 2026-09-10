"""Join the existing Beta AI and email verification migration histories.

Revision ID: 93d48b10560a
Revises: 6b9674012543, e4c7a1b90f32
"""

revision = "93d48b10560a"
down_revision = ("6b9674012543", "e4c7a1b90f32")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Join histories without changing tables or data."""


def downgrade() -> None:
    """Separate histories without changing tables or data."""
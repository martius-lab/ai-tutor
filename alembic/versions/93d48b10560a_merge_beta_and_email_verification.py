"""Join this Level AI test stage with the email verification history."""

revision = "93d48b10560a"
down_revision = ("5377527607bc", "e4c7a1b90f32")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Join histories without table or data changes."""


def downgrade() -> None:
    """Separate histories without table or data changes."""

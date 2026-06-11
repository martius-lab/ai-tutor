"""add account email tokens

Revision ID: 9f1b2c3d4e5f
Revises: 7d4104f6fd42
Create Date: 2026-05-22 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = "9f1b2c3d4e5f"
down_revision: Union[str, None] = "7d4104f6fd42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "accountemailtoken",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("token_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["localuser.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("accountemailtoken", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_accountemailtoken_purpose"), ["purpose"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_accountemailtoken_token_hash"), ["token_hash"], unique=True
        )
        batch_op.create_index(
            batch_op.f("ix_accountemailtoken_user_id"), ["user_id"], unique=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("accountemailtoken", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_accountemailtoken_user_id"))
        batch_op.drop_index(batch_op.f("ix_accountemailtoken_token_hash"))
        batch_op.drop_index(batch_op.f("ix_accountemailtoken_purpose"))

    op.drop_table("accountemailtoken")

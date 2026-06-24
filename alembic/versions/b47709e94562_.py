"""Add lecture_id to reports

Revision ID: b47709e94562
Revises: c9782a9331d4
Create Date: 2026-06-16 22:57:10.832404

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b47709e94562"
down_revision: Union[str, None] = "c9782a9331d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Need to disable foreign key constraints for SQLite. SQLite recreates tables
    # for batch alters, and active foreign keys can interfere with table rebuilds.
    conn = op.get_bind()
    if conn.engine.name.startswith("sqlite"):
        conn.execute(sa.text("PRAGMA foreign_keys=OFF"))

    with op.batch_alter_table("report", schema=None) as batch_op:
        batch_op.add_column(sa.Column("lecture_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_report_lecture_id"), ["lecture_id"], unique=False
        )

    # Backfill lecture_id for existing reports while exercise_id still points to the
    # original exercise. Reports whose exercise was already deleted cannot be recovered.
    op.execute(
        """
        UPDATE report
        SET lecture_id = (
            SELECT exercise.lecture_id
            FROM exercise
            WHERE exercise.id = report.exercise_id
        )
        WHERE exercise_id IS NOT NULL
        """
    )

    with op.batch_alter_table("report", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "fk_report_lecture_id_lecture",
            "lecture",
            ["lecture_id"],
            ["id"],
            ondelete="CASCADE",
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Need to disable foreign key constraints for SQLite. SQLite recreates tables
    # for batch alters, and active foreign keys can interfere with table rebuilds.
    conn = op.get_bind()
    if conn.engine.name.startswith("sqlite"):
        conn.execute(sa.text("PRAGMA foreign_keys=OFF"))

    with op.batch_alter_table("report", schema=None) as batch_op:
        batch_op.drop_constraint(
            "fk_report_lecture_id_lecture", type_="foreignkey"
        )
        batch_op.drop_index(batch_op.f("ix_report_lecture_id"))
        batch_op.drop_column("lecture_id")

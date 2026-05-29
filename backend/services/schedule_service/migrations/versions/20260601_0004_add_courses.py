"""add courses

Revision ID: 20260601_0004
Revises: 20260601_0003
Create Date: 2026-06-01 00:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260601_0004"
down_revision: Union[str, Sequence[str], None] = "20260601_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("programme_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["programme_id"], ["programmes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "course_instructors",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.BigInteger(), nullable=False),
        sa.Column("instructor_id", sa.BigInteger(), nullable=False),
        sa.Column("instructor_name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("schedule_items", sa.Column("course_id", sa.BigInteger(), nullable=True))
    op.create_index("ix_schedule_items_course_id", "schedule_items", ["course_id"])
    op.create_foreign_key(
        "fk_schedule_items_course_id_courses",
        "schedule_items",
        "courses",
        ["course_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_schedule_items_course_id_courses", "schedule_items", type_="foreignkey")
    op.drop_index("ix_schedule_items_course_id", table_name="schedule_items")
    op.drop_column("schedule_items", "course_id")
    op.drop_table("course_instructors")
    op.drop_table("courses")

"""add schedule item booking id

Revision ID: 20260601_0003
Revises: 20260601_0002
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260601_0003"
down_revision: Union[str, Sequence[str], None] = "20260601_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "schedule_items",
        sa.Column("booking_id", sa.BigInteger(), nullable=True),
    )
    op.create_index(
        "ix_schedule_items_booking_id",
        "schedule_items",
        ["booking_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_schedule_items_booking_id", table_name="schedule_items")
    op.drop_column("schedule_items", "booking_id")

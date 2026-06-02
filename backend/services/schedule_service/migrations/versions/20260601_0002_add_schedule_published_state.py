"""add schedule published state

Revision ID: 20260601_0002
Revises: 20260601_0001
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260601_0002"
down_revision: Union[str, Sequence[str], None] = "20260601_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "schedules",
        sa.Column(
            "is_published",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("schedules", "is_published", server_default=None)


def downgrade() -> None:
    op.drop_column("schedules", "is_published")

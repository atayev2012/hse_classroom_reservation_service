"""create notification history

Revision ID: 20260601_0001
Revises:
Create Date: 2026-06-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260601_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notification_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recipient_email", sa.String(length=320), nullable=False),
        sa.Column("notification_type", sa.String(length=80), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_notification_history_notification_type"),
        "notification_history",
        ["notification_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_history_recipient_email"),
        "notification_history",
        ["recipient_email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_history_status"),
        "notification_history",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_notification_history_status"), table_name="notification_history")
    op.drop_index(op.f("ix_notification_history_recipient_email"), table_name="notification_history")
    op.drop_index(op.f("ix_notification_history_notification_type"), table_name="notification_history")
    op.drop_table("notification_history")

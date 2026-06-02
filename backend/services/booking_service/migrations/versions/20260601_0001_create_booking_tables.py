"""create booking tables

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
        "buildings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("address", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_buildings_name"), "buildings", ["name"], unique=True)

    op.create_table(
        "equipment",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "rooms",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("building_id", sa.BigInteger(), nullable=False),
        sa.Column("room_number", sa.String(), nullable=False),
        sa.Column("is_zoom", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("building_id", "room_number", name="uq_building_room_number"),
    )

    op.create_table(
        "bookings",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("event_title", sa.String(), nullable=False),
        sa.Column("event_description", sa.String(), nullable=True),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("event_time_slot", sa.String(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("building_id", sa.BigInteger(), nullable=False),
        sa.Column("room_id", sa.BigInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["building_id"], ["buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "building_id",
            "room_id",
            "event_date",
            "event_time_slot",
            name="uq_room_booking_slot",
        ),
    )

    op.create_table(
        "room_equipment",
        sa.Column("room_id", sa.BigInteger(), nullable=False),
        sa.Column("equipment_id", sa.BigInteger(), nullable=False),
        sa.Column("equipment_qty", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("room_id", "equipment_id"),
    )


def downgrade() -> None:
    op.drop_table("room_equipment")
    op.drop_table("bookings")
    op.drop_table("rooms")
    op.drop_table("equipment")
    op.drop_index(op.f("ix_buildings_name"), table_name="buildings")
    op.drop_table("buildings")

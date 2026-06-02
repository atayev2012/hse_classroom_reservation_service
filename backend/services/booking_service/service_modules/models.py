from __future__ import annotations

from database import Base

from sqlalchemy import BigInteger, String, ForeignKey, Boolean, Integer, UniqueConstraint, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date

# Building model
class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    address: Mapped[str] = mapped_column(String, nullable=False)

    # Building can have zero or many rooms.
    rooms: Mapped[list[Room]] = relationship(
        back_populates="building",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    bookings: Mapped[list[Booking]] = relationship(
        back_populates="building",
        passive_deletes=True,
    )

# Classroom model
class Room(Base):
    __tablename__ = "rooms"

    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "room_number",
            name="uq_building_room_number"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # Every room must belong to one building.
    # A building can still exist without rooms.
    building_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    room_number: Mapped[str] = mapped_column(String, nullable=False)
    is_zoom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    building: Mapped[Building] = relationship(back_populates="rooms")
    # Room can have zero or many equipment associations.
    equipment_associations: Mapped[list[RoomEquipment]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    bookings: Mapped[list[Booking]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

# Classroom equipment model
class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    # Equipment can be assigned to zero or many rooms.
    room_associations: Mapped[list[RoomEquipment]] = relationship(
        back_populates="equipment",
        passive_deletes=True,
    )

# Room and equipement association model
class RoomEquipment(Base):
    __tablename__ = "room_equipment"

    room_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True)
    equipment_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("equipment.id", ondelete="CASCADE"), primary_key=True)
    equipment_qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Relationships
    room: Mapped[Room] = relationship(back_populates="equipment_associations")
    equipment: Mapped[Equipment] = relationship(back_populates="room_associations")


# Booking model
class Booking(Base):
    __tablename__ = "bookings"

    __table_args__ = (
        UniqueConstraint(
            "building_id",
            "room_id",
            "event_date",
            "event_time_slot",
            name="uq_room_booking_slot"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    event_title: Mapped[str] = mapped_column(String, nullable=False)
    event_description: Mapped[str | None] = mapped_column(String, nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    event_time_slot: Mapped[str] = mapped_column(String, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    building_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False)
    room_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    building: Mapped[Building] = relationship(back_populates="bookings")
    room: Mapped[Room] = relationship(back_populates="bookings")

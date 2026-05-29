from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any, Generic, TypeVar

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from service_modules.models import (
    Booking,
    Building,
    Equipment,
    Room,
    RoomEquipment,
)

ModelType = TypeVar("ModelType")


class BaseDAO(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **data: Any) -> ModelType:
        instance = self.model(**data)

        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)

        return instance

    async def get_by_id(self, object_id: int) -> ModelType | None:
        return await self.session.get(self.model, object_id)

    async def get_one_or_none(self, **filters: Any) -> ModelType | None:
        stmt = select(self.model).filter_by(**filters)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> Sequence[ModelType]:
        stmt = (
            select(self.model)
            .filter_by(**filters)
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_by_id(self, object_id: int, **data: Any) -> ModelType | None:
        instance = await self.get_by_id(object_id)

        if instance is None:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(instance, key, value)

        await self.session.commit()
        await self.session.refresh(instance)

        return instance

    async def delete_by_id(self, object_id: int) -> bool:
        instance = await self.get_by_id(object_id)

        if instance is None:
            return False

        await self.session.delete(instance)
        await self.session.commit()

        return True

    async def exists(self, **filters: Any) -> bool:
        stmt = select(self.model).filter_by(**filters).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)

        result = await self.session.execute(stmt)
        return result.scalar_one()


class BuildingDAO(BaseDAO[Building]):
    model = Building

    @staticmethod
    def _load_rooms():
        return selectinload(Building.rooms)

    @staticmethod
    def _load_bookings():
        return selectinload(Building.bookings)

    @staticmethod
    def _load_full():
        return (
            selectinload(Building.rooms)
            .selectinload(Room.equipment_associations)
            .selectinload(RoomEquipment.equipment),
            selectinload(Building.bookings).selectinload(Booking.room),
        )

    async def create_building(
        self,
        name: str,
        address: str,
    ) -> Building:
        building = Building(
            name=name,
            address=address,
        )

        self.session.add(building)
        await self.session.commit()
        await self.session.refresh(building)

        return building

    async def get_building_by_id(
        self,
        building_id: int,
        load_rooms: bool = False,
        load_bookings: bool = False,
        load_full: bool = False,
    ) -> Building | None:
        stmt = select(Building).where(Building.id == building_id)

        if load_full:
            stmt = stmt.options(*self._load_full())
        else:
            if load_rooms:
                stmt = stmt.options(self._load_rooms())
            if load_bookings:
                stmt = stmt.options(self._load_bookings())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_building_by_name(
        self,
        name: str,
        load_rooms: bool = False,
        load_bookings: bool = False,
        load_full: bool = False,
    ) -> Building | None:
        stmt = select(Building).where(Building.name == name)

        if load_full:
            stmt = stmt.options(*self._load_full())
        else:
            if load_rooms:
                stmt = stmt.options(self._load_rooms())
            if load_bookings:
                stmt = stmt.options(self._load_bookings())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_buildings(
        self,
        limit: int = 100,
        offset: int = 0,
        load_rooms: bool = False,
        load_bookings: bool = False,
    ) -> Sequence[Building]:
        stmt = select(Building).limit(limit).offset(offset)

        if load_rooms:
            stmt = stmt.options(self._load_rooms())

        if load_bookings:
            stmt = stmt.options(self._load_bookings())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_building(
        self,
        building_id: int,
        name: str | None = None,
        address: str | None = None,
    ) -> Building | None:
        building = await self.get_building_by_id(building_id)

        if building is None:
            return None

        if name is not None:
            building.name = name

        if address is not None:
            building.address = address

        await self.session.commit()
        await self.session.refresh(building)

        return building

    async def delete_building(self, building_id: int) -> bool:
        building = await self.get_building_by_id(building_id)

        if building is None:
            return False

        await self.session.delete(building)
        await self.session.commit()

        return True


class RoomDAO(BaseDAO[Room]):
    model = Room

    @staticmethod
    def _load_building():
        return selectinload(Room.building)

    @staticmethod
    def _load_equipment():
        return (
            selectinload(Room.equipment_associations)
            .selectinload(RoomEquipment.equipment)
        )

    @staticmethod
    def _load_bookings():
        return selectinload(Room.bookings)

    @staticmethod
    def _load_full():
        return (
            selectinload(Room.building),
            selectinload(Room.equipment_associations).selectinload(
                RoomEquipment.equipment
            ),
            selectinload(Room.bookings),
        )

    async def create_room(
        self,
        building_id: int,
        room_number: str,
        is_zoom: bool = False,
        is_active: bool = True,
    ) -> Room:
        room = Room(
            building_id=building_id,
            room_number=room_number,
            is_zoom=is_zoom,
            is_active=is_active,
        )

        self.session.add(room)
        await self.session.commit()
        await self.session.refresh(room)

        return room

    async def get_room_by_id(
        self,
        room_id: int,
        load_building: bool = False,
        load_equipment: bool = False,
        load_bookings: bool = False,
        load_full: bool = False,
    ) -> Room | None:
        stmt = select(Room).where(Room.id == room_id)

        if load_full:
            stmt = stmt.options(*self._load_full())
        else:
            if load_building:
                stmt = stmt.options(self._load_building())
            if load_equipment:
                stmt = stmt.options(self._load_equipment())
            if load_bookings:
                stmt = stmt.options(self._load_bookings())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_room_by_building_and_number(
        self,
        building_id: int,
        room_number: str,
        load_full: bool = False,
    ) -> Room | None:
        stmt = select(Room).where(
            Room.building_id == building_id,
            Room.room_number == room_number,
        )

        if load_full:
            stmt = stmt.options(*self._load_full())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_rooms(
        self,
        building_id: int | None = None,
        is_active: bool | None = None,
        is_zoom: bool | None = None,
        limit: int = 100,
        offset: int = 0,
        load_building: bool = False,
        load_equipment: bool = False,
        load_bookings: bool = False,
    ) -> Sequence[Room]:
        stmt = select(Room)

        if building_id is not None:
            stmt = stmt.where(Room.building_id == building_id)

        if is_active is not None:
            stmt = stmt.where(Room.is_active == is_active)

        if is_zoom is not None:
            stmt = stmt.where(Room.is_zoom == is_zoom)

        if load_building:
            stmt = stmt.options(self._load_building())

        if load_equipment:
            stmt = stmt.options(self._load_equipment())

        if load_bookings:
            stmt = stmt.options(self._load_bookings())

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_room(
        self,
        room_id: int,
        building_id: int | None = None,
        room_number: str | None = None,
        is_zoom: bool | None = None,
        is_active: bool | None = None,
    ) -> Room | None:
        room = await self.get_room_by_id(room_id)

        if room is None:
            return None

        if building_id is not None:
            room.building_id = building_id

        if room_number is not None:
            room.room_number = room_number

        if is_zoom is not None:
            room.is_zoom = is_zoom

        if is_active is not None:
            room.is_active = is_active

        await self.session.commit()
        await self.session.refresh(room)

        return room

    async def activate_room(self, room_id: int) -> bool:
        room = await self.get_room_by_id(room_id)

        if room is None:
            return False

        room.is_active = True
        await self.session.commit()

        return True

    async def deactivate_room(self, room_id: int) -> bool:
        room = await self.get_room_by_id(room_id)

        if room is None:
            return False

        room.is_active = False
        await self.session.commit()

        return True

    async def delete_room(self, room_id: int) -> bool:
        room = await self.get_room_by_id(room_id)

        if room is None:
            return False

        await self.session.delete(room)
        await self.session.commit()

        return True


class EquipmentDAO(BaseDAO[Equipment]):
    model = Equipment

    @staticmethod
    def _load_rooms():
        return (
            selectinload(Equipment.room_associations)
            .selectinload(RoomEquipment.room)
            .selectinload(Room.building)
        )

    async def create_equipment(
        self,
        name: str,
        description: str | None = None,
    ) -> Equipment:
        equipment = Equipment(
            name=name,
            description=description,
        )

        self.session.add(equipment)
        await self.session.commit()
        await self.session.refresh(equipment)

        return equipment

    async def get_equipment_by_id(
        self,
        equipment_id: int,
        load_rooms: bool = False,
    ) -> Equipment | None:
        stmt = select(Equipment).where(Equipment.id == equipment_id)

        if load_rooms:
            stmt = stmt.options(self._load_rooms())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_equipment_by_name(
        self,
        name: str,
        load_rooms: bool = False,
    ) -> Equipment | None:
        stmt = select(Equipment).where(Equipment.name == name)

        if load_rooms:
            stmt = stmt.options(self._load_rooms())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_equipment_list(
        self,
        limit: int = 100,
        offset: int = 0,
        load_rooms: bool = False,
    ) -> Sequence[Equipment]:
        stmt = select(Equipment).limit(limit).offset(offset)

        if load_rooms:
            stmt = stmt.options(self._load_rooms())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_equipment(
        self,
        equipment_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> Equipment | None:
        equipment = await self.get_equipment_by_id(equipment_id)

        if equipment is None:
            return None

        if name is not None:
            equipment.name = name

        if description is not None:
            equipment.description = description

        await self.session.commit()
        await self.session.refresh(equipment)

        return equipment

    async def delete_equipment(self, equipment_id: int) -> bool:
        equipment = await self.get_equipment_by_id(equipment_id)

        if equipment is None:
            return False

        await self.session.delete(equipment)
        await self.session.commit()

        return True


class RoomEquipmentDAO(BaseDAO[RoomEquipment]):
    model = RoomEquipment

    @staticmethod
    def _load_full():
        return (
            selectinload(RoomEquipment.room).selectinload(Room.building),
            selectinload(RoomEquipment.equipment),
        )

    async def assign_equipment_to_room(
        self,
        room_id: int,
        equipment_id: int,
        equipment_qty: int = 1,
    ) -> RoomEquipment:
        existing = await self.get_room_equipment(
            room_id=room_id,
            equipment_id=equipment_id,
        )

        if existing is not None:
            existing.equipment_qty = equipment_qty
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        association = RoomEquipment(
            room_id=room_id,
            equipment_id=equipment_id,
            equipment_qty=equipment_qty,
        )

        self.session.add(association)
        await self.session.commit()
        await self.session.refresh(association)

        return association

    async def get_room_equipment(
        self,
        room_id: int,
        equipment_id: int,
        load_full: bool = False,
    ) -> RoomEquipment | None:
        stmt = select(RoomEquipment).where(
            RoomEquipment.room_id == room_id,
            RoomEquipment.equipment_id == equipment_id,
        )

        if load_full:
            stmt = stmt.options(*self._load_full())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_equipment_for_room(
        self,
        room_id: int,
        load_equipment: bool = True,
    ) -> Sequence[RoomEquipment]:
        stmt = select(RoomEquipment).where(RoomEquipment.room_id == room_id)

        if load_equipment:
            stmt = stmt.options(selectinload(RoomEquipment.equipment))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_rooms_with_equipment(
        self,
        equipment_id: int,
        load_room: bool = True,
    ) -> Sequence[RoomEquipment]:
        stmt = select(RoomEquipment).where(
            RoomEquipment.equipment_id == equipment_id
        )

        if load_room:
            stmt = stmt.options(
                selectinload(RoomEquipment.room).selectinload(Room.building)
            )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_equipment_quantity(
        self,
        room_id: int,
        equipment_id: int,
        equipment_qty: int,
    ) -> RoomEquipment | None:
        association = await self.get_room_equipment(
            room_id=room_id,
            equipment_id=equipment_id,
        )

        if association is None:
            return None

        association.equipment_qty = equipment_qty

        await self.session.commit()
        await self.session.refresh(association)

        return association

    async def remove_equipment_from_room(
        self,
        room_id: int,
        equipment_id: int,
    ) -> bool:
        association = await self.get_room_equipment(
            room_id=room_id,
            equipment_id=equipment_id,
        )

        if association is None:
            return False

        await self.session.delete(association)
        await self.session.commit()

        return True

    async def clear_room_equipment(self, room_id: int) -> int:
        associations = await self.get_equipment_for_room(
            room_id=room_id,
            load_equipment=False,
        )

        deleted_count = len(associations)

        for association in associations:
            await self.session.delete(association)

        await self.session.commit()

        return deleted_count


class BookingDAO(BaseDAO[Booking]):
    model = Booking

    @staticmethod
    def _load_building():
        return selectinload(Booking.building)

    @staticmethod
    def _load_room():
        return selectinload(Booking.room)

    @staticmethod
    def _load_full():
        return (
            selectinload(Booking.building),
            selectinload(Booking.room).selectinload(Room.equipment_associations),
        )

    async def is_room_available(
        self,
        room_id: int,
        event_date: date,
        event_time_slot: str,
        exclude_booking_id: int | None = None,
    ) -> bool:
        conditions = [
            Booking.room_id == room_id,
            Booking.event_date == event_date,
            Booking.event_time_slot == event_time_slot,
            Booking.is_active.is_(True),
            Booking.is_deleted.is_(False),
        ]

        if exclude_booking_id is not None:
            conditions.append(Booking.id != exclude_booking_id)

        stmt = select(Booking).where(and_(*conditions)).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is None

    async def create_booking(
        self,
        event_type: str,
        event_title: str,
        event_date: date,
        event_time_slot: str,
        user_id: int,
        building_id: int,
        room_id: int,
        event_description: str | None = None,
    ) -> Booking:
        room_stmt = select(Room).where(Room.id == room_id)
        room_result = await self.session.execute(room_stmt)
        room = room_result.scalar_one_or_none()

        if room is None:
            raise ValueError("Room does not exist.")

        if room.building_id != building_id:
            raise ValueError("Room does not belong to the selected building.")

        duplicate_stmt = select(Booking).where(
            Booking.building_id == building_id,
            Booking.room_id == room_id,
            Booking.event_date == event_date,
            Booking.event_time_slot == event_time_slot,
        )
        duplicate_result = await self.session.execute(duplicate_stmt)
        duplicate = duplicate_result.scalar_one_or_none()

        if duplicate is not None:
            if duplicate.is_active and not duplicate.is_deleted:
                raise ValueError("Room is already booked for this date and time slot.")

            duplicate.event_type = event_type
            duplicate.event_title = event_title
            duplicate.event_description = event_description
            duplicate.user_id = user_id
            duplicate.is_active = True
            duplicate.is_deleted = False
            await self.session.commit()
            await self.session.refresh(duplicate)
            return duplicate

        is_available = await self.is_room_available(
            room_id=room_id,
            event_date=event_date,
            event_time_slot=event_time_slot,
        )

        if not is_available:
            raise ValueError("Room is already booked for this date and time slot.")

        booking = Booking(
            event_type=event_type,
            event_title=event_title,
            event_description=event_description,
            event_date=event_date,
            event_time_slot=event_time_slot,
            user_id=user_id,
            building_id=building_id,
            room_id=room_id,
            is_active=True,
            is_deleted=False,
        )

        self.session.add(booking)
        await self.session.commit()
        await self.session.refresh(booking)

        return booking

    async def get_booking_by_id(
        self,
        booking_id: int,
        load_building: bool = False,
        load_room: bool = False,
        load_full: bool = False,
    ) -> Booking | None:
        stmt = select(Booking).where(Booking.id == booking_id)

        if load_full:
            stmt = stmt.options(*self._load_full())
        else:
            if load_building:
                stmt = stmt.options(self._load_building())
            if load_room:
                stmt = stmt.options(self._load_room())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_bookings(
        self,
        building_id: int | None = None,
        room_id: int | None = None,
        user_id: int | None = None,
        event_date: date | None = None,
        event_time_slot: str | None = None,
        is_active: bool | None = None,
        is_deleted: bool | None = False,
        limit: int = 100,
        offset: int = 0,
        load_building: bool = False,
        load_room: bool = False,
    ) -> Sequence[Booking]:
        stmt = select(Booking)

        if building_id is not None:
            stmt = stmt.where(Booking.building_id == building_id)

        if room_id is not None:
            stmt = stmt.where(Booking.room_id == room_id)

        if user_id is not None:
            stmt = stmt.where(Booking.user_id == user_id)

        if event_date is not None:
            stmt = stmt.where(Booking.event_date == event_date)

        if event_time_slot is not None:
            stmt = stmt.where(Booking.event_time_slot == event_time_slot)

        if is_active is not None:
            stmt = stmt.where(Booking.is_active == is_active)

        if is_deleted is not None:
            stmt = stmt.where(Booking.is_deleted == is_deleted)

        if load_building:
            stmt = stmt.options(self._load_building())

        if load_room:
            stmt = stmt.options(self._load_room())

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_bookings_for_room_on_date(
        self,
        room_id: int,
        event_date: date,
        load_room: bool = False,
    ) -> Sequence[Booking]:
        return await self.get_bookings(
            room_id=room_id,
            event_date=event_date,
            is_active=True,
            is_deleted=False,
            load_room=load_room,
        )

    async def update_booking(
        self,
        booking_id: int,
        event_type: str | None = None,
        event_title: str | None = None,
        event_description: str | None = None,
        event_date: date | None = None,
        event_time_slot: str | None = None,
        user_id: int | None = None,
        building_id: int | None = None,
        room_id: int | None = None,
        is_active: bool | None = None,
    ) -> Booking | None:
        booking = await self.get_booking_by_id(booking_id)

        if booking is None:
            return None

        new_building_id = building_id if building_id is not None else booking.building_id
        new_room_id = room_id if room_id is not None else booking.room_id
        new_event_date = event_date if event_date is not None else booking.event_date
        new_time_slot = (
            event_time_slot if event_time_slot is not None else booking.event_time_slot
        )

        room_stmt = select(Room).where(Room.id == new_room_id)
        room_result = await self.session.execute(room_stmt)
        room = room_result.scalar_one_or_none()

        if room is None:
            raise ValueError("Room does not exist.")

        if room.building_id != new_building_id:
            raise ValueError("Room does not belong to the selected building.")

        is_available = await self.is_room_available(
            room_id=new_room_id,
            event_date=new_event_date,
            event_time_slot=new_time_slot,
            exclude_booking_id=booking_id,
        )

        if not is_available:
            raise ValueError("Room is already booked for this date and time slot.")

        if event_type is not None:
            booking.event_type = event_type

        if event_title is not None:
            booking.event_title = event_title

        if event_description is not None:
            booking.event_description = event_description

        if event_date is not None:
            booking.event_date = event_date

        if event_time_slot is not None:
            booking.event_time_slot = event_time_slot

        if user_id is not None:
            booking.user_id = user_id

        if building_id is not None:
            booking.building_id = building_id

        if room_id is not None:
            booking.room_id = room_id

        if is_active is not None:
            booking.is_active = is_active

        await self.session.commit()
        await self.session.refresh(booking)

        return booking

    async def cancel_booking(self, booking_id: int) -> bool:
        booking = await self.get_booking_by_id(booking_id)

        if booking is None:
            return False

        booking.is_active = False

        await self.session.commit()

        return True

    async def restore_booking(self, booking_id: int) -> bool:
        booking = await self.get_booking_by_id(booking_id)

        if booking is None:
            return False

        booking.is_active = True
        booking.is_deleted = False

        await self.session.commit()

        return True

    async def soft_delete_booking(self, booking_id: int) -> bool:
        booking = await self.get_booking_by_id(booking_id)

        if booking is None:
            return False

        booking.is_active = False
        booking.is_deleted = True

        await self.session.commit()

        return True

    async def hard_delete_booking(self, booking_id: int) -> bool:
        booking = await self.get_booking_by_id(booking_id)

        if booking is None:
            return False

        await self.session.delete(booking)
        await self.session.commit()

        return True


class BookingServiceDAO:
    """
    Facade DAO for the booking microservice.

    Use this class in your service layer when you want all DAO classes
    available through one shared AsyncSession.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

        self.buildings = BuildingDAO(session)
        self.rooms = RoomDAO(session)
        self.equipment = EquipmentDAO(session)
        self.room_equipment = RoomEquipmentDAO(session)
        self.bookings = BookingDAO(session)

    async def get_full_building(self, building_id: int) -> Building | None:
        return await self.buildings.get_building_by_id(
            building_id=building_id,
            load_full=True,
        )

    async def get_full_room(self, room_id: int) -> Room | None:
        return await self.rooms.get_room_by_id(
            room_id=room_id,
            load_full=True,
        )

    async def get_full_booking(self, booking_id: int) -> Booking | None:
        return await self.bookings.get_booking_by_id(
            booking_id=booking_id,
            load_full=True,
        )

    async def create_room_with_equipment(
        self,
        building_id: int,
        room_number: str,
        equipment_items: list[dict[str, int]],
        is_zoom: bool = False,
        is_active: bool = True,
    ) -> Room:
        room = await self.rooms.create_room(
            building_id=building_id,
            room_number=room_number,
            is_zoom=is_zoom,
            is_active=is_active,
        )

        for item in equipment_items:
            await self.room_equipment.assign_equipment_to_room(
                room_id=room.id,
                equipment_id=item["equipment_id"],
                equipment_qty=item.get("equipment_qty", 1),
            )

        return await self.rooms.get_room_by_id(
            room_id=room.id,
            load_full=True,
        )

    async def replace_room_equipment(
        self,
        room_id: int,
        equipment_items: list[dict[str, int]],
    ) -> Room | None:
        room = await self.rooms.get_room_by_id(room_id)

        if room is None:
            return None

        await self.room_equipment.clear_room_equipment(room_id)

        for item in equipment_items:
            await self.room_equipment.assign_equipment_to_room(
                room_id=room_id,
                equipment_id=item["equipment_id"],
                equipment_qty=item.get("equipment_qty", 1),
            )

        return await self.rooms.get_room_by_id(
            room_id=room_id,
            load_full=True,
        )

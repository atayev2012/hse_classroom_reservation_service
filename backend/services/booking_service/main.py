from __future__ import annotations

import asyncio
import logging
import logging.config
from datetime import date
from pathlib import Path

import booking_service_pb2
import booking_service_pb2_grpc
import grpc

from database import async_session_maker
from service_modules.config import LOGGING_CONFIG, service_config
from service_modules.db_utils import BookingServiceDAO
from service_modules.models import Booking, Building, Equipment, Room

Path("logs").mkdir(exist_ok=True)
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("booking_microservice")


class BookingService(booking_service_pb2_grpc.BookingServiceServicer):
    def __init__(self, session_factory=async_session_maker):
        self.session_factory = session_factory

    async def HealthCheck(self, request, context):
        try:
            return booking_service_pb2.HealthCheckResponse(
                success=True,
                status="SERVING",
            )
        except asyncio.TimeoutError:
            logger.exception("Booking service health check timed out")
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Health check timed out")
            return booking_service_pb2.HealthCheckResponse(
                success=False,
                status="TIMEOUT",
            )
        except Exception as exc:
            logger.exception("Booking service health check failed")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(str(exc))
            return booking_service_pb2.HealthCheckResponse(
                success=False,
                status="UNAVAILABLE",
            )

    async def AddBuilding(self, request, context):
        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            building = await dao.buildings.create_building(
                name=request.name,
                address=request.address,
            )

        return booking_service_pb2.BuildingResponse(
            success=True,
            status="Created",
            building=_building_to_proto(building),
        )

    async def UpdateBuilding(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            building = await dao.buildings.update_building(
                building_id=request.id,
                name=_optional_value(request, "name"),
                address=_optional_value(request, "address"),
            )

        if building is None:
            return booking_service_pb2.BuildingResponse(
                success=False,
                status="Building not found",
            )

        return booking_service_pb2.BuildingResponse(
            success=True,
            status="Updated",
            building=_building_to_proto(building),
        )

    async def DeleteBuilding(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            success = await dao.buildings.delete_building(request.id)

        return booking_service_pb2.BuildingResponse(
            success=success,
            status="Deleted" if success else "Building not found",
        )

    async def GetAllBuildings(self, request, context):
        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            buildings = await dao.buildings.get_buildings(load_rooms=True)

        return booking_service_pb2.AllBuildingsResponse(
            success=True,
            status="OK",
            buildings=[_building_to_proto(building) for building in buildings],
        )

    async def GetSingleBuilding(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            building = await dao.get_full_building(request.id)

        if building is None:
            return booking_service_pb2.BuildingResponse(
                success=False,
                status="Building not found",
            )

        return booking_service_pb2.BuildingResponse(
            success=True,
            status="OK",
            building=_building_to_proto(building),
        )

    async def AddRoom(self, request, context):
        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            try:
                equipment_items = await _equipment_items_from_proto(dao, request.equipment)
            except ValueError as exc:
                return booking_service_pb2.RoomResponse(
                    success=False,
                    status=str(exc),
                )
            room = await dao.create_room_with_equipment(
                building_id=request.building_id,
                room_number=request.room_number,
                equipment_items=equipment_items,
                is_zoom=_optional_value(request, "is_zoom", False),
                is_active=_optional_value(request, "is_active", True),
            )

        return booking_service_pb2.RoomResponse(
            success=True,
            status="Created",
            room=_room_to_proto(room),
        )

    async def UpdateRoom(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            room = await dao.rooms.update_room(
                room_id=request.id,
                building_id=_optional_value(request, "building_id"),
                room_number=_optional_value(request, "room_number"),
                is_zoom=_optional_value(request, "is_zoom"),
                is_active=_optional_value(request, "is_active"),
            )

            if room is not None and _optional_value(request, "replace_equipment", False):
                try:
                    equipment_items = await _equipment_items_from_proto(
                        dao,
                        request.equipment,
                    )
                except ValueError as exc:
                    return booking_service_pb2.RoomResponse(
                        success=False,
                        status=str(exc),
                    )
                room = await dao.replace_room_equipment(room.id, equipment_items)
            elif room is not None:
                room = await dao.get_full_room(room.id)

        if room is None:
            return booking_service_pb2.RoomResponse(
                success=False,
                status="Room not found",
            )

        return booking_service_pb2.RoomResponse(
            success=True,
            status="Updated",
            room=_room_to_proto(room),
        )

    async def DeleteRoom(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            success = await dao.rooms.delete_room(request.id)

        return booking_service_pb2.RoomResponse(
            success=success,
            status="Deleted" if success else "Room not found",
        )

    async def GetAllRooms(self, request, context):
        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            rooms = await dao.rooms.get_rooms(
                building_id=_optional_value(request, "id"),
                load_equipment=True,
            )

        return booking_service_pb2.AllRoomsResponse(
            success=True,
            status="OK",
            rooms=[_room_to_proto(room) for room in rooms],
        )

    async def GetSingleRoom(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            room = await dao.get_full_room(request.id)

        if room is None:
            return booking_service_pb2.RoomResponse(
                success=False,
                status="Room not found",
            )

        return booking_service_pb2.RoomResponse(
            success=True,
            status="OK",
            room=_room_to_proto(room),
        )

    async def AddEquipment(self, request, context):
        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            equipment = await dao.equipment.create_equipment(
                name=request.name,
                description=_optional_value(request, "description"),
            )

        return booking_service_pb2.EquipmentResponse(
            success=True,
            status="Created",
            equipment=_equipment_to_proto(equipment),
        )

    async def UpdateEquipment(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            equipment = await dao.equipment.update_equipment(
                equipment_id=request.id,
                name=_optional_value(request, "name"),
                description=_optional_value(request, "description"),
            )

        if equipment is None:
            return booking_service_pb2.EquipmentResponse(
                success=False,
                status="Equipment not found",
            )

        return booking_service_pb2.EquipmentResponse(
            success=True,
            status="Updated",
            equipment=_equipment_to_proto(equipment),
        )

    async def DeleteEquipment(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            success = await dao.equipment.delete_equipment(request.id)

        return booking_service_pb2.EquipmentResponse(
            success=success,
            status="Deleted" if success else "Equipment not found",
        )

    async def GetAllEquipment(self, request, context):
        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            equipment = await dao.equipment.get_equipment_list()

        return booking_service_pb2.AllEquipmentResponse(
            success=True,
            status="OK",
            equipment=[_equipment_to_proto(item) for item in equipment],
        )

    async def GetSingleEquipment(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            equipment = await dao.equipment.get_equipment_by_id(request.id)

        if equipment is None:
            return booking_service_pb2.EquipmentResponse(
                success=False,
                status="Equipment not found",
            )

        return booking_service_pb2.EquipmentResponse(
            success=True,
            status="OK",
            equipment=_equipment_to_proto(equipment),
        )

    async def AddBooking(self, request, context):
        time_slot = _first_time_slot(request)

        if time_slot is None:
            await context.abort(
                grpc.StatusCode.INVALID_ARGUMENT,
                "event_time_slot is required",
            )

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            try:
                booking = await dao.bookings.create_booking(
                    event_type=request.event_type,
                    event_title=request.event_title,
                    event_description=_optional_value(request, "event_description"),
                    event_date=_parse_date(request.event_date),
                    event_time_slot=time_slot,
                    user_id=request.user_id,
                    building_id=request.building_id,
                    room_id=request.room_id,
                )
                booking = await dao.get_full_booking(booking.id)
            except ValueError as exc:
                return booking_service_pb2.BookingResponse(
                    success=False,
                    status=str(exc),
                )

        return booking_service_pb2.BookingResponse(
            success=True,
            status="Created",
            booking=_booking_to_proto(booking),
        )

    async def UpdateBooking(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            try:
                booking = await dao.bookings.update_booking(
                    booking_id=request.id,
                    event_type=_optional_value(request, "event_type"),
                    event_title=_optional_value(request, "event_title"),
                    event_description=_optional_value(request, "event_description"),
                    event_date=_parse_date(request.event_date)
                    if _has_field(request, "event_date")
                    else None,
                    event_time_slot=_first_time_slot(request),
                    user_id=_optional_value(request, "user_id"),
                    building_id=_optional_value(request, "building_id"),
                    room_id=_optional_value(request, "room_id"),
                    is_active=_optional_value(request, "is_active"),
                )
                if booking is not None:
                    booking = await dao.get_full_booking(booking.id)
            except ValueError as exc:
                return booking_service_pb2.BookingResponse(
                    success=False,
                    status=str(exc),
                )

        if booking is None:
            return booking_service_pb2.BookingResponse(
                success=False,
                status="Booking not found",
            )

        return booking_service_pb2.BookingResponse(
            success=True,
            status="Updated",
            booking=_booking_to_proto(booking),
        )

    async def DeleteBooking(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            success = await dao.bookings.soft_delete_booking(request.id)

        return booking_service_pb2.BookingResponse(
            success=success,
            status="Deleted" if success else "Booking not found",
        )

    async def GetAllBookings(self, request, context):
        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            bookings: list[Booking] = []
            timeslots = list(request.timeslots)

            if timeslots:
                seen_ids = set()
                for timeslot in timeslots:
                    rows = await dao.bookings.get_bookings(
                        building_id=_optional_value(request, "building_id"),
                        room_id=_optional_value(request, "room_id"),
                        user_id=_optional_value(request, "user_id"),
                        event_date=_parse_date(request.event_date)
                        if _has_field(request, "event_date")
                        else None,
                        event_time_slot=timeslot,
                        load_building=True,
                        load_room=True,
                    )
                    for row in rows:
                        if row.id not in seen_ids:
                            seen_ids.add(row.id)
                            bookings.append(row)
            else:
                bookings = list(
                    await dao.bookings.get_bookings(
                        building_id=_optional_value(request, "building_id"),
                        room_id=_optional_value(request, "room_id"),
                        user_id=_optional_value(request, "user_id"),
                        event_date=_parse_date(request.event_date)
                        if _has_field(request, "event_date")
                        else None,
                        load_building=True,
                        load_room=True,
                    )
                )

        return booking_service_pb2.AllBookingsResponse(
            success=True,
            status="OK",
            bookings=[_booking_to_proto(booking) for booking in bookings],
        )

    async def GetSingleBooking(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = BookingServiceDAO(session)
            booking = await dao.get_full_booking(request.id)

        if booking is None:
            return booking_service_pb2.BookingResponse(
                success=False,
                status="Booking not found",
            )

        return booking_service_pb2.BookingResponse(
            success=True,
            status="OK",
            booking=_booking_to_proto(booking),
        )


async def _equipment_items_from_proto(
    dao: BookingServiceDAO,
    equipment_messages,
) -> list[dict[str, int]]:
    items = []

    for item in equipment_messages:
        equipment = await dao.equipment.get_equipment_by_name(item.name)

        if equipment is None:
            raise ValueError(f"Equipment '{item.name}' does not exist.")

        items.append(
            {
                "equipment_id": equipment.id,
                "equipment_qty": item.qty or 1,
            }
        )

    return items


def _building_to_proto(building: Building):
    return booking_service_pb2.Building(
        id=building.id,
        name=building.name,
        address=building.address,
        rooms=[_room_to_proto(room) for room in building.__dict__.get("rooms", [])],
    )


def _room_to_proto(room: Room):
    equipment = []

    for association in room.__dict__.get("equipment_associations", []) or []:
        if association.equipment is not None:
            equipment.append(
                booking_service_pb2.Equipment(
                    name=association.equipment.name,
                    qty=association.equipment_qty,
                )
            )

    return booking_service_pb2.Room(
        id=room.id,
        building_id=room.building_id,
        room_number=room.room_number,
        equipment=equipment,
        is_zoom=room.is_zoom,
        is_active=room.is_active,
    )


def _equipment_to_proto(equipment: Equipment):
    equipment_proto = booking_service_pb2.Equipment(
        id=equipment.id,
        name=equipment.name,
        qty=1,
    )

    if equipment.description is not None:
        equipment_proto.description = equipment.description

    return equipment_proto


def _booking_to_proto(booking: Booking):
    booking_proto = booking_service_pb2.Booking(
        id=booking.id,
        event_type=booking.event_type,
        event_title=booking.event_title,
        event_date=booking.event_date.isoformat(),
        event_time_slot=[booking.event_time_slot],
        user_id=booking.user_id,
        building_id=booking.building_id,
        room_id=booking.room_id,
        is_active=booking.is_active,
        is_deleted=booking.is_deleted,
    )

    if booking.event_description is not None:
        booking_proto.event_description = booking.event_description

    return booking_proto


def _has_field(message, field_name: str) -> bool:
    try:
        return message.HasField(field_name)
    except ValueError:
        return bool(getattr(message, field_name))


def _optional_value(message, field_name: str, default=None):
    return getattr(message, field_name) if _has_field(message, field_name) else default


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _first_time_slot(request) -> str | None:
    return request.event_time_slot[0] if request.event_time_slot else None


async def serve() -> None:
    server = grpc.aio.server()
    booking_service_pb2_grpc.add_BookingServiceServicer_to_server(
        BookingService(),
        server,
    )

    listen_addr = f"{service_config.HOST}:{service_config.PORT}"
    server.add_insecure_port(listen_addr)

    await server.start()
    logger.info("Booking service started at %s", listen_addr)
    await server.wait_for_termination()


if __name__ == "__main__":
    asyncio.run(serve())

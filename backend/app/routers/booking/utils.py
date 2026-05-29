from __future__ import annotations

import booking_service_pb2

from .schemas import BookingCreateRequest, BookingUpdateRequest, BuildingCreateRequest, BuildingUpdateRequest, EquipmentCreateRequest, EquipmentUpdateRequest, RoomCreateRequest, RoomUpdateRequest


def building_create_to_proto(payload: BuildingCreateRequest) -> booking_service_pb2.Building:
    return booking_service_pb2.Building(name=payload.name, address=payload.address)


def building_update_to_proto(building_id: int, payload: BuildingUpdateRequest) -> booking_service_pb2.Building:
    building = booking_service_pb2.Building(id=building_id)
    if payload.name is not None:
        building.name = payload.name
    if payload.address is not None:
        building.address = payload.address
    return building


def room_create_to_proto(payload: RoomCreateRequest) -> booking_service_pb2.Room:
    return booking_service_pb2.Room(
        building_id=payload.building_id,
        room_number=payload.room_number,
        equipment=[
            booking_service_pb2.Equipment(name=item.name, qty=item.qty)
            for item in payload.equipment
        ],
        is_zoom=payload.is_zoom,
        is_active=payload.is_active,
    )


def room_update_to_proto(room_id: int, payload: RoomUpdateRequest) -> booking_service_pb2.Room:
    room = booking_service_pb2.Room(id=room_id)
    if payload.building_id is not None:
        room.building_id = payload.building_id
    if payload.room_number is not None:
        room.room_number = payload.room_number
    if payload.equipment is not None:
        room.replace_equipment = True
        room.equipment.extend(
            booking_service_pb2.Equipment(name=item.name, qty=item.qty)
            for item in payload.equipment
        )
    if payload.is_zoom is not None:
        room.is_zoom = payload.is_zoom
    if payload.is_active is not None:
        room.is_active = payload.is_active
    return room


def equipment_create_to_proto(payload: EquipmentCreateRequest) -> booking_service_pb2.Equipment:
    equipment = booking_service_pb2.Equipment(name=payload.name)
    if payload.description is not None:
        equipment.description = payload.description
    return equipment


def equipment_update_to_proto(equipment_id: int, payload: EquipmentUpdateRequest) -> booking_service_pb2.Equipment:
    equipment = booking_service_pb2.Equipment(id=equipment_id)
    if payload.name is not None:
        equipment.name = payload.name
    if payload.description is not None:
        equipment.description = payload.description
    return equipment


def booking_create_to_proto(payload: BookingCreateRequest) -> booking_service_pb2.Booking:
    return booking_service_pb2.Booking(
        event_type=payload.event_type,
        event_title=payload.event_title,
        event_description=payload.event_description or "",
        event_date=payload.event_date,
        event_time_slot=payload.event_time_slot,
        user_id=payload.user_id or 0,
        building_id=payload.building_id,
        room_id=payload.room_id,
    )


def booking_update_to_proto(booking_id: int, payload: BookingUpdateRequest) -> booking_service_pb2.Booking:
    booking = booking_service_pb2.Booking(id=booking_id)
    for field_name in (
        "event_type",
        "event_title",
        "event_description",
        "event_date",
        "user_id",
        "building_id",
        "room_id",
        "is_active",
    ):
        value = getattr(payload, field_name)
        if value is not None:
            setattr(booking, field_name, value)
    if payload.event_time_slot is not None:
        booking.event_time_slot.extend(payload.event_time_slot)
    return booking

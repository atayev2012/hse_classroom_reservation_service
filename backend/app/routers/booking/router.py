from __future__ import annotations

import booking_service_pb2
from fastapi import APIRouter, Depends, Request

from dependencies import require_roles
from grpc_utils import proto_to_dict
from health import check_grpc_health

from .schemas import BookingCreateRequest, BookingUpdateRequest, BuildingCreateRequest, BuildingUpdateRequest, EquipmentCreateRequest, EquipmentUpdateRequest, RoomCreateRequest, RoomUpdateRequest
from .utils import booking_create_to_proto, booking_update_to_proto, building_create_to_proto, building_update_to_proto, equipment_create_to_proto, equipment_update_to_proto, room_create_to_proto, room_update_to_proto

router = APIRouter(
    prefix="/booking",
    tags=["booking"],
    dependencies=[Depends(require_roles("employee", "manager", "admin"))],
)


def _paginate(response: dict, key: str, limit: int | None, offset: int | None) -> dict:
    rows = response.get(key, [])
    start = max(offset or 0, 0)
    page_size = max(limit or len(rows) or 1, 1)
    return {
        **response,
        key: rows[start:start + page_size],
        "total_count": len(rows),
        "limit": page_size,
        "offset": start,
    }


@router.get("/health")
async def health(request: Request):
    return await check_grpc_health(
        request.app.state.booking_stub,
        booking_service_pb2.HealthCheckRequest(),
        "booking service",
    )


@router.get("/buildings")
async def get_buildings(
    request: Request,
    limit: int | None = None,
    offset: int | None = 0,
):
    response = await request.app.state.booking_stub.GetAllBuildings(
        booking_service_pb2.Empty()
    )
    return _paginate(proto_to_dict(response), "buildings", limit, offset)


@router.get("/buildings/{building_id}")
async def get_building(building_id: int, request: Request):
    response = await request.app.state.booking_stub.GetSingleBuilding(
        booking_service_pb2.Building(id=building_id)
    )
    return proto_to_dict(response)


@router.post("/buildings")
async def add_building(payload: BuildingCreateRequest, request: Request):
    response = await request.app.state.booking_stub.AddBuilding(
        building_create_to_proto(payload)
    )
    return proto_to_dict(response)


@router.patch("/buildings/{building_id}")
async def update_building(
    building_id: int,
    payload: BuildingUpdateRequest,
    request: Request,
):
    response = await request.app.state.booking_stub.UpdateBuilding(
        building_update_to_proto(building_id, payload)
    )
    return proto_to_dict(response)


@router.delete("/buildings/{building_id}")
async def delete_building(building_id: int, request: Request):
    response = await request.app.state.booking_stub.DeleteBuilding(
        booking_service_pb2.Building(id=building_id)
    )
    return proto_to_dict(response)


@router.get("/rooms")
async def get_rooms(
    request: Request,
    building_id: int | None = None,
    limit: int | None = None,
    offset: int | None = 0,
):
    grpc_request = booking_service_pb2.Building()
    if building_id is not None:
        grpc_request.id = building_id
    response = await request.app.state.booking_stub.GetAllRooms(grpc_request)
    return _paginate(proto_to_dict(response), "rooms", limit, offset)


@router.get("/rooms/{room_id}")
async def get_room(room_id: int, request: Request):
    response = await request.app.state.booking_stub.GetSingleRoom(
        booking_service_pb2.Room(id=room_id)
    )
    return proto_to_dict(response)


@router.post("/rooms")
async def add_room(payload: RoomCreateRequest, request: Request):
    response = await request.app.state.booking_stub.AddRoom(room_create_to_proto(payload))
    return proto_to_dict(response)


@router.patch("/rooms/{room_id}")
async def update_room(room_id: int, payload: RoomUpdateRequest, request: Request):
    response = await request.app.state.booking_stub.UpdateRoom(
        room_update_to_proto(room_id, payload)
    )
    return proto_to_dict(response)


@router.delete("/rooms/{room_id}")
async def delete_room(room_id: int, request: Request):
    response = await request.app.state.booking_stub.DeleteRoom(
        booking_service_pb2.Room(id=room_id)
    )
    return proto_to_dict(response)


@router.get("/equipment")
async def get_equipment(
    request: Request,
    limit: int | None = None,
    offset: int | None = 0,
):
    response = await request.app.state.booking_stub.GetAllEquipment(
        booking_service_pb2.Empty()
    )
    return _paginate(proto_to_dict(response), "equipment", limit, offset)


@router.get("/equipment/{equipment_id}")
async def get_single_equipment(equipment_id: int, request: Request):
    response = await request.app.state.booking_stub.GetSingleEquipment(
        booking_service_pb2.Equipment(id=equipment_id)
    )
    return proto_to_dict(response)


@router.post("/equipment")
async def add_equipment(payload: EquipmentCreateRequest, request: Request):
    response = await request.app.state.booking_stub.AddEquipment(
        equipment_create_to_proto(payload)
    )
    return proto_to_dict(response)


@router.patch("/equipment/{equipment_id}")
async def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdateRequest,
    request: Request,
):
    response = await request.app.state.booking_stub.UpdateEquipment(
        equipment_update_to_proto(equipment_id, payload)
    )
    return proto_to_dict(response)


@router.delete("/equipment/{equipment_id}")
async def delete_equipment(equipment_id: int, request: Request):
    response = await request.app.state.booking_stub.DeleteEquipment(
        booking_service_pb2.Equipment(id=equipment_id)
    )
    return proto_to_dict(response)


@router.get("/bookings")
async def get_bookings(
    request: Request,
    building_id: int | None = None,
    room_id: int | None = None,
    event_date: str | None = None,
    user_id: int | None = None,
    limit: int | None = None,
    offset: int | None = 0,
):
    grpc_request = booking_service_pb2.AllBookingsRequest()
    if building_id is not None:
        grpc_request.building_id = building_id
    if room_id is not None:
        grpc_request.room_id = room_id
    if event_date is not None:
        grpc_request.event_date = event_date
    if user_id is not None:
        grpc_request.user_id = user_id
    response = await request.app.state.booking_stub.GetAllBookings(grpc_request)
    data = proto_to_dict(response)
    data["bookings"] = sorted(
        data.get("bookings", []),
        key=lambda booking: (booking.get("event_date", ""), booking.get("id", 0)),
        reverse=True,
    )
    return _paginate(data, "bookings", limit, offset)


@router.get("/bookings/{booking_id}")
async def get_booking(booking_id: int, request: Request):
    response = await request.app.state.booking_stub.GetSingleBooking(
        booking_service_pb2.Booking(id=booking_id)
    )
    return proto_to_dict(response)


@router.post("/bookings")
async def add_booking(payload: BookingCreateRequest, request: Request):
    response = await request.app.state.booking_stub.AddBooking(
        booking_create_to_proto(payload)
    )
    return proto_to_dict(response)


@router.patch("/bookings/{booking_id}")
async def update_booking(
    booking_id: int,
    payload: BookingUpdateRequest,
    request: Request,
):
    response = await request.app.state.booking_stub.UpdateBooking(
        booking_update_to_proto(booking_id, payload)
    )
    return proto_to_dict(response)


@router.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: int, request: Request):
    response = await request.app.state.booking_stub.DeleteBooking(
        booking_service_pb2.Booking(id=booking_id)
    )
    return proto_to_dict(response)

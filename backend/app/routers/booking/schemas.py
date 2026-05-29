from __future__ import annotations

from pydantic import BaseModel


class EquipmentRequest(BaseModel):
    name: str
    qty: int


class EquipmentCreateRequest(BaseModel):
    name: str
    description: str | None = None


class EquipmentUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class BuildingCreateRequest(BaseModel):
    name: str
    address: str


class BuildingUpdateRequest(BaseModel):
    name: str | None = None
    address: str | None = None


class RoomCreateRequest(BaseModel):
    building_id: int
    room_number: str
    equipment: list[EquipmentRequest] = []
    is_zoom: bool = False
    is_active: bool = True


class RoomUpdateRequest(BaseModel):
    building_id: int | None = None
    room_number: str | None = None
    equipment: list[EquipmentRequest] | None = None
    is_zoom: bool | None = None
    is_active: bool | None = None


class BookingCreateRequest(BaseModel):
    event_type: str
    event_title: str
    event_description: str | None = None
    event_date: str
    event_time_slot: list[str]
    user_id: int | None = None
    building_id: int
    room_id: int


class BookingUpdateRequest(BaseModel):
    event_type: str | None = None
    event_title: str | None = None
    event_description: str | None = None
    event_date: str | None = None
    event_time_slot: list[str] | None = None
    user_id: int | None = None
    building_id: int | None = None
    room_id: int | None = None
    is_active: bool | None = None

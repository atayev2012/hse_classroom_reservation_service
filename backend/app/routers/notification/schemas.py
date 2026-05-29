from __future__ import annotations

from pydantic import BaseModel, EmailStr


class ReservationNotificationRequest(BaseModel):
    building_name: str
    room_number: str
    event_date: str
    time_slot: str
    status: str
    email: EmailStr


class VerificationCodeNotificationRequest(BaseModel):
    email: EmailStr
    code: str
    verification_url: str
    code_valid_till: str
    ip_address: str = ""
    request_datetime: str = ""
    device_info: str = ""


class LoginSuccessfulNotificationRequest(BaseModel):
    email: EmailStr
    ip_address: str = ""
    request_datetime: str = ""
    device_info: str = ""

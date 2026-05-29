from __future__ import annotations

import notification_service_pb2

from .schemas import LoginSuccessfulNotificationRequest, ReservationNotificationRequest, VerificationCodeNotificationRequest


def reservation_to_proto(payload: ReservationNotificationRequest) -> notification_service_pb2.ReservationNotificationRequest:
    return notification_service_pb2.ReservationNotificationRequest(
        building_name=payload.building_name,
        room_number=payload.room_number,
        event_date=payload.event_date,
        time_slot=payload.time_slot,
        status=payload.status,
        email=payload.email,
    )


def verification_to_proto(payload: VerificationCodeNotificationRequest) -> notification_service_pb2.VerificationCodeRequest:
    return notification_service_pb2.VerificationCodeRequest(
        email=payload.email,
        code=payload.code,
        verification_url=payload.verification_url,
        code_valid_till=payload.code_valid_till,
        ip_address=payload.ip_address,
        request_datetime=payload.request_datetime,
        device_info=payload.device_info,
    )


def login_success_to_proto(payload: LoginSuccessfulNotificationRequest) -> notification_service_pb2.LoginSuccessfulRequest:
    return notification_service_pb2.LoginSuccessfulRequest(
        email=payload.email,
        ip_address=payload.ip_address,
        request_datetime=payload.request_datetime,
        device_info=payload.device_info,
    )

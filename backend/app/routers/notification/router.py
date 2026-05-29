from __future__ import annotations

import notification_service_pb2
from fastapi import APIRouter, Depends, Request

from dependencies import require_roles
from grpc_utils import proto_to_dict
from health import check_grpc_health

from .schemas import LoginSuccessfulNotificationRequest, ReservationNotificationRequest, VerificationCodeNotificationRequest
from .utils import login_success_to_proto, reservation_to_proto, verification_to_proto

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/health")
async def health(request: Request):
    return await check_grpc_health(
        request.app.state.notification_stub,
        notification_service_pb2.HealthCheckRequest(),
        "notification service",
    )


@router.post("/reservation")
async def send_reservation_notification(
    payload: ReservationNotificationRequest,
    request: Request,
    _: dict = Depends(require_roles("employee", "manager", "admin")),
):
    response = await request.app.state.notification_stub.SendReservationNotification(
        reservation_to_proto(payload)
    )
    return proto_to_dict(response)


@router.post("/verification-code")
async def send_verification_code(
    payload: VerificationCodeNotificationRequest,
    request: Request,
    _: dict = Depends(require_roles("admin")),
):
    response = await request.app.state.notification_stub.SendVerificationCode(
        verification_to_proto(payload)
    )
    return proto_to_dict(response)


@router.post("/login-successful")
async def send_login_successful(
    payload: LoginSuccessfulNotificationRequest,
    request: Request,
    _: dict = Depends(require_roles("admin")),
):
    response = await request.app.state.notification_stub.SendLoginSuccessful(
        login_success_to_proto(payload)
    )
    return proto_to_dict(response)

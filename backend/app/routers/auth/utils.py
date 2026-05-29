from __future__ import annotations

from datetime import datetime, timezone

import auth_service_pb2
from fastapi import Request

from .schemas import UserCreateRequest, UserUpdateRequest


def request_ip(request: Request) -> str:
    return request.client.host if request.client else ""


def request_datetime() -> str:
    return datetime.now(timezone.utc).isoformat()


def device_info(request: Request, explicit: str | None) -> str:
    return explicit or request.headers.get("user-agent", "")


def user_create_to_proto(payload: UserCreateRequest) -> auth_service_pb2.User:
    user = auth_service_pb2.User(
        email=payload.email,
        type=payload.type,
        first_name=payload.first_name or "",
        last_name=payload.last_name or "",
        middle_name=payload.middle_name or "",
        is_active=payload.is_active,
    )
    if payload.student_profile is not None:
        user.student_profile.CopyFrom(
            auth_service_pb2.StudentProfile(
                group_name=payload.student_profile.group_name or "",
                study_program=payload.student_profile.study_program or "",
            )
        )
    if payload.employee_profile is not None:
        user.employee_profile.CopyFrom(
            auth_service_pb2.EmployeeProfile(
                department_name=payload.employee_profile.department_name or "",
                position=payload.employee_profile.position or "",
            )
        )
    return user


def user_update_to_proto(user_id: int, payload: UserUpdateRequest) -> auth_service_pb2.User:
    user = auth_service_pb2.User(id=user_id)
    for field_name in (
        "email",
        "type",
        "first_name",
        "last_name",
        "middle_name",
        "is_active",
        "is_deleted",
    ):
        value = getattr(payload, field_name)
        if value is not None:
            setattr(user, field_name, value)

    if payload.student_profile is not None:
        user.student_profile.CopyFrom(
            auth_service_pb2.StudentProfile(
                group_name=payload.student_profile.group_name or "",
                study_program=payload.student_profile.study_program or "",
            )
        )
    if payload.employee_profile is not None:
        user.employee_profile.CopyFrom(
            auth_service_pb2.EmployeeProfile(
                department_name=payload.employee_profile.department_name or "",
                position=payload.employee_profile.position or "",
            )
        )
    return user

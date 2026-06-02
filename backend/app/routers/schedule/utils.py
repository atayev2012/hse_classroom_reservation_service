from __future__ import annotations

import schedule_service_pb2
from fastapi import HTTPException, Request, status

from .schemas import (
    AcademicYearCreateRequest,
    AcademicYearUpdateRequest,
    CourseCreateRequest,
    CourseUpdateRequest,
    GroupCreateRequest,
    GroupStudentRequest,
    GroupStudentUpdateRequest,
    GroupUpdateRequest,
    HolidayCreateRequest,
    HolidayUpdateRequest,
    ModuleCreateRequest,
    ModuleUpdateRequest,
    ProgrammeCreateRequest,
    ProgrammeUpdateRequest,
    ScheduleCreateRequest,
    ScheduleItemCreateRequest,
    ScheduleItemUpdateRequest,
    ScheduleUpdateRequest,
)


async def group_id_for_student(request: Request, user: dict) -> int:
    group_name = user.get("student_profile", {}).get("group_name")
    if not group_name:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student group is not assigned",
        )

    response = await request.app.state.schedule_stub.GetAllGroups(
        schedule_service_pb2.AllGroupsRequest(limit=1000)
    )
    for group in response.groups:
        if group.name == group_name:
            return group.id

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Student group was not found in schedule service",
    )


def academic_year_create_to_proto(payload: AcademicYearCreateRequest) -> schedule_service_pb2.AcademicYear:
    return schedule_service_pb2.AcademicYear(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )


def academic_year_update_to_proto(item_id: int, payload: AcademicYearUpdateRequest) -> schedule_service_pb2.AcademicYear:
    proto = schedule_service_pb2.AcademicYear(id=item_id)
    _set_optional(proto, payload, ("name", "start_date", "end_date"))
    return proto


def module_create_to_proto(payload: ModuleCreateRequest) -> schedule_service_pb2.Module:
    return schedule_service_pb2.Module(
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        academic_year_id=payload.academic_year_id,
    )


def module_update_to_proto(item_id: int, payload: ModuleUpdateRequest) -> schedule_service_pb2.Module:
    proto = schedule_service_pb2.Module(id=item_id)
    _set_optional(proto, payload, ("name", "start_date", "end_date", "academic_year_id"))
    return proto


def holiday_create_to_proto(payload: HolidayCreateRequest) -> schedule_service_pb2.Holiday:
    return schedule_service_pb2.Holiday(
        date=payload.date,
        name=payload.name or "",
        description=payload.description or "",
        academic_year_id=payload.academic_year_id,
    )


def holiday_update_to_proto(item_id: int, payload: HolidayUpdateRequest) -> schedule_service_pb2.Holiday:
    proto = schedule_service_pb2.Holiday(id=item_id)
    _set_optional(proto, payload, ("date", "name", "description", "academic_year_id"))
    return proto


def programme_create_to_proto(payload: ProgrammeCreateRequest) -> schedule_service_pb2.Programme:
    return schedule_service_pb2.Programme(
        name=payload.name,
        description=payload.description or "",
    )


def programme_update_to_proto(item_id: int, payload: ProgrammeUpdateRequest) -> schedule_service_pb2.Programme:
    proto = schedule_service_pb2.Programme(id=item_id)
    _set_optional(proto, payload, ("name", "description"))
    return proto


def course_create_to_proto(payload: CourseCreateRequest) -> schedule_service_pb2.Course:
    return schedule_service_pb2.Course(
        name=payload.name,
        description=payload.description or "",
        programme_id=payload.programme_id,
        instructors=[
            schedule_service_pb2.CourseInstructor(
                instructor_id=instructor.instructor_id,
                instructor_name=instructor.instructor_name,
            )
            for instructor in payload.instructors
        ],
    )


def course_update_to_proto(item_id: int, payload: CourseUpdateRequest) -> schedule_service_pb2.Course:
    proto = schedule_service_pb2.Course(id=item_id)
    _set_optional(proto, payload, ("name", "description", "programme_id"))
    if payload.instructors is not None:
        proto.instructors.extend([
            schedule_service_pb2.CourseInstructor(
                instructor_id=instructor.instructor_id,
                instructor_name=instructor.instructor_name,
            )
            for instructor in payload.instructors
        ])
    return proto


def group_create_to_proto(payload: GroupCreateRequest) -> schedule_service_pb2.Group:
    return schedule_service_pb2.Group(
        name=payload.name,
        email=payload.email,
        programme_id=payload.programme_id,
        students=[
            schedule_service_pb2.GroupStudent(
                user_id=student.user_id,
                user_email=student.user_email,
            )
            for student in payload.students
        ],
    )


def group_update_to_proto(item_id: int, payload: GroupUpdateRequest) -> schedule_service_pb2.Group:
    proto = schedule_service_pb2.Group(id=item_id)
    _set_optional(proto, payload, ("name", "email", "programme_id"))
    return proto


def group_student_create_to_proto(group_id: int, payload: GroupStudentRequest) -> schedule_service_pb2.GroupStudent:
    return schedule_service_pb2.GroupStudent(
        user_id=payload.user_id,
        user_email=payload.user_email,
        group_id=group_id,
    )


def group_student_update_to_proto(user_id: int, payload: GroupStudentUpdateRequest) -> schedule_service_pb2.GroupStudent:
    proto = schedule_service_pb2.GroupStudent(user_id=user_id)
    _set_optional(proto, payload, ("user_email", "group_id"))
    return proto


def schedule_create_to_proto(payload: ScheduleCreateRequest) -> schedule_service_pb2.Schedule:
    return schedule_service_pb2.Schedule(
        name=payload.name,
        module_id=payload.module_id,
        group_id=payload.group_id,
    )


def schedule_update_to_proto(item_id: int, payload: ScheduleUpdateRequest) -> schedule_service_pb2.Schedule:
    proto = schedule_service_pb2.Schedule(id=item_id)
    _set_optional(proto, payload, ("name", "module_id", "group_id", "is_published"))
    return proto


def schedule_item_create_to_proto(payload: ScheduleItemCreateRequest) -> schedule_service_pb2.ScheduleItem:
    proto = schedule_service_pb2.ScheduleItem(
        title=payload.title,
        item_type=payload.item_type,
        instructor_id=payload.instructor_id,
        instructor_name=payload.instructor_name,
        building_id=payload.building_id,
        building_address=payload.building_address,
        room_id=payload.room_id,
        room_number=payload.room_number,
        date=payload.date,
        time_slot=payload.time_slot,
        schedule_id=payload.schedule_id,
    )
    if payload.booking_id is not None:
        proto.booking_id = payload.booking_id
    if payload.course_id is not None:
        proto.course_id = payload.course_id
    return proto


def schedule_item_update_to_proto(item_id: int, payload: ScheduleItemUpdateRequest) -> schedule_service_pb2.ScheduleItem:
    proto = schedule_service_pb2.ScheduleItem(id=item_id)
    _set_optional(
        proto,
        payload,
        (
            "title",
            "item_type",
            "course_id",
            "instructor_id",
            "instructor_name",
            "building_id",
            "building_address",
            "room_id",
            "room_number",
            "date",
            "time_slot",
            "schedule_id",
            "booking_id",
        ),
    )
    return proto


def _set_optional(proto, payload, field_names: tuple[str, ...]) -> None:
    for field_name in field_names:
        value = getattr(payload, field_name)
        if value is not None:
            setattr(proto, field_name, value)

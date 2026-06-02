from __future__ import annotations

import schedule_service_pb2
from fastapi import APIRouter, Depends, HTTPException, Request, status

from dependencies import get_current_user, require_roles
from grpc_utils import proto_to_dict
from health import check_grpc_health

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
from .utils import (
    academic_year_create_to_proto,
    academic_year_update_to_proto,
    course_create_to_proto,
    course_update_to_proto,
    group_create_to_proto,
    group_id_for_student,
    group_student_create_to_proto,
    group_student_update_to_proto,
    group_update_to_proto,
    holiday_create_to_proto,
    holiday_update_to_proto,
    module_create_to_proto,
    module_update_to_proto,
    programme_create_to_proto,
    programme_update_to_proto,
    schedule_create_to_proto,
    schedule_item_create_to_proto,
    schedule_item_update_to_proto,
    schedule_update_to_proto,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("/health")
async def health(request: Request):
    return await check_grpc_health(
        request.app.state.schedule_stub,
        schedule_service_pb2.HealthCheckRequest(),
        "schedule service",
    )


@router.get("")
async def get_schedules(
    request: Request,
    group_id: int | None = None,
    module_id: int | None = None,
    personal: bool = False,
    user: dict = Depends(get_current_user),
):
    role = user.get("role")
    if role == "student":
        group_id = group_id or await group_id_for_student(request, user)
        grpc_request = schedule_service_pb2.AllSchedulesRequest(
            group_id=group_id,
            is_published=True,
            limit=1000,
        )
        if module_id is not None:
            grpc_request.module_id = module_id
        response = await request.app.state.schedule_stub.GetAllSchedules(grpc_request)
        return proto_to_dict(response)

    if role == "employee" and personal:
        response = await request.app.state.schedule_stub.GetAllScheduleItems(
            schedule_service_pb2.AllScheduleItemsRequest(
                instructor_id=int(user["id"]),
                limit=1000,
            )
        )
        return proto_to_dict(response)

    if role == "employee" and group_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="group_id is required unless personal=true",
        )

    grpc_request = schedule_service_pb2.AllSchedulesRequest(limit=1000)
    if group_id is not None:
        grpc_request.group_id = group_id
    if module_id is not None:
        grpc_request.module_id = module_id
    if role in {"student", "employee"}:
        grpc_request.is_published = True
    response = await request.app.state.schedule_stub.GetAllSchedules(grpc_request)
    return proto_to_dict(response)


@router.post("")
async def add_schedule(payload: ScheduleCreateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.AddSchedule(schedule_create_to_proto(payload))
    return proto_to_dict(response)


@router.get("/academic-years")
async def get_academic_years(request: Request, limit: int = 100, offset: int = 0):
    response = await request.app.state.schedule_stub.GetAllAcademicYears(
        schedule_service_pb2.AllAcademicYearsRequest(limit=limit, offset=offset)
    )
    return proto_to_dict(response)


@router.get("/academic-years/{item_id}")
async def get_academic_year(item_id: int, request: Request):
    response = await request.app.state.schedule_stub.GetSingleAcademicYear(schedule_service_pb2.AcademicYear(id=item_id))
    return proto_to_dict(response)


@router.post("/academic-years")
async def add_academic_year(payload: AcademicYearCreateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.AddAcademicYear(academic_year_create_to_proto(payload))
    return proto_to_dict(response)


@router.patch("/academic-years/{item_id}")
async def update_academic_year(item_id: int, payload: AcademicYearUpdateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.UpdateAcademicYear(academic_year_update_to_proto(item_id, payload))
    return proto_to_dict(response)


@router.delete("/academic-years/{item_id}")
async def delete_academic_year(item_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.DeleteAcademicYear(schedule_service_pb2.AcademicYear(id=item_id))
    return proto_to_dict(response)


@router.get("/modules")
async def get_modules(request: Request, academic_year_id: int | None = None, active_on: str | None = None, limit: int = 100, offset: int = 0):
    grpc_request = schedule_service_pb2.AllModulesRequest(limit=limit, offset=offset)
    if academic_year_id is not None:
        grpc_request.academic_year_id = academic_year_id
    if active_on is not None:
        grpc_request.active_on = active_on
    response = await request.app.state.schedule_stub.GetAllModules(grpc_request)
    return proto_to_dict(response)


@router.get("/modules/{item_id}")
async def get_module(item_id: int, request: Request):
    response = await request.app.state.schedule_stub.GetSingleModule(schedule_service_pb2.Module(id=item_id))
    return proto_to_dict(response)


@router.post("/modules")
async def add_module(payload: ModuleCreateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.AddModule(module_create_to_proto(payload))
    return proto_to_dict(response)


@router.patch("/modules/{item_id}")
async def update_module(item_id: int, payload: ModuleUpdateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.UpdateModule(module_update_to_proto(item_id, payload))
    return proto_to_dict(response)


@router.delete("/modules/{item_id}")
async def delete_module(item_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.DeleteModule(schedule_service_pb2.Module(id=item_id))
    return proto_to_dict(response)


@router.get("/holidays")
async def get_holidays(request: Request, academic_year_id: int | None = None, date_from: str | None = None, date_to: str | None = None, limit: int = 100, offset: int = 0):
    grpc_request = schedule_service_pb2.AllHolidaysRequest(limit=limit, offset=offset)
    if academic_year_id is not None:
        grpc_request.academic_year_id = academic_year_id
    if date_from is not None:
        grpc_request.date_from = date_from
    if date_to is not None:
        grpc_request.date_to = date_to
    response = await request.app.state.schedule_stub.GetAllHolidays(grpc_request)
    return proto_to_dict(response)


@router.get("/holidays/{item_id}")
async def get_holiday(item_id: int, request: Request):
    response = await request.app.state.schedule_stub.GetSingleHoliday(schedule_service_pb2.Holiday(id=item_id))
    return proto_to_dict(response)


@router.post("/holidays")
async def add_holiday(payload: HolidayCreateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.AddHoliday(holiday_create_to_proto(payload))
    return proto_to_dict(response)


@router.patch("/holidays/{item_id}")
async def update_holiday(item_id: int, payload: HolidayUpdateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.UpdateHoliday(holiday_update_to_proto(item_id, payload))
    return proto_to_dict(response)


@router.delete("/holidays/{item_id}")
async def delete_holiday(item_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.DeleteHoliday(schedule_service_pb2.Holiday(id=item_id))
    return proto_to_dict(response)


@router.get("/programmes")
async def get_programmes(request: Request, limit: int = 100, offset: int = 0):
    response = await request.app.state.schedule_stub.GetAllProgrammes(
        schedule_service_pb2.AllProgrammesRequest(limit=limit, offset=offset)
    )
    return proto_to_dict(response)


@router.get("/programmes/{item_id}")
async def get_programme(item_id: int, request: Request):
    response = await request.app.state.schedule_stub.GetSingleProgramme(schedule_service_pb2.Programme(id=item_id))
    return proto_to_dict(response)


@router.post("/programmes")
async def add_programme(payload: ProgrammeCreateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.AddProgramme(programme_create_to_proto(payload))
    return proto_to_dict(response)


@router.patch("/programmes/{item_id}")
async def update_programme(item_id: int, payload: ProgrammeUpdateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.UpdateProgramme(programme_update_to_proto(item_id, payload))
    return proto_to_dict(response)


@router.delete("/programmes/{item_id}")
async def delete_programme(item_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.DeleteProgramme(schedule_service_pb2.Programme(id=item_id))
    return proto_to_dict(response)


@router.get("/courses")
async def get_courses(request: Request, programme_id: int | None = None, instructor_id: int | None = None, limit: int = 100, offset: int = 0):
    grpc_request = schedule_service_pb2.AllCoursesRequest(limit=limit, offset=offset)
    if programme_id is not None:
        grpc_request.programme_id = programme_id
    if instructor_id is not None:
        grpc_request.instructor_id = instructor_id
    response = await request.app.state.schedule_stub.GetAllCourses(grpc_request)
    return proto_to_dict(response)


@router.get("/courses/{item_id}")
async def get_course(item_id: int, request: Request):
    response = await request.app.state.schedule_stub.GetSingleCourse(schedule_service_pb2.Course(id=item_id))
    return proto_to_dict(response)


@router.post("/courses")
async def add_course(payload: CourseCreateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.AddCourse(course_create_to_proto(payload))
    return proto_to_dict(response)


@router.patch("/courses/{item_id}")
async def update_course(item_id: int, payload: CourseUpdateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.UpdateCourse(course_update_to_proto(item_id, payload))
    return proto_to_dict(response)


@router.delete("/courses/{item_id}")
async def delete_course(item_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.DeleteCourse(schedule_service_pb2.Course(id=item_id))
    return proto_to_dict(response)


@router.get("/groups")
async def get_groups(request: Request, programme_id: int | None = None, limit: int = 100, offset: int = 0):
    grpc_request = schedule_service_pb2.AllGroupsRequest(limit=limit, offset=offset)
    if programme_id is not None:
        grpc_request.programme_id = programme_id
    response = await request.app.state.schedule_stub.GetAllGroups(grpc_request)
    return proto_to_dict(response)


@router.get("/groups/{item_id}")
async def get_group(item_id: int, request: Request):
    response = await request.app.state.schedule_stub.GetSingleGroup(schedule_service_pb2.Group(id=item_id))
    return proto_to_dict(response)


@router.post("/groups")
async def add_group(payload: GroupCreateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.AddGroup(group_create_to_proto(payload))
    return proto_to_dict(response)


@router.patch("/groups/{item_id}")
async def update_group(item_id: int, payload: GroupUpdateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.UpdateGroup(group_update_to_proto(item_id, payload))
    return proto_to_dict(response)


@router.delete("/groups/{item_id}")
async def delete_group(item_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.DeleteGroup(schedule_service_pb2.Group(id=item_id))
    return proto_to_dict(response)


@router.get("/groups/{group_id}/students")
async def get_group_students(group_id: int, request: Request, limit: int = 100, offset: int = 0):
    response = await request.app.state.schedule_stub.GetAllGroupStudents(
        schedule_service_pb2.AllGroupStudentsRequest(group_id=group_id, limit=limit, offset=offset)
    )
    return proto_to_dict(response)


@router.post("/groups/{group_id}/students")
async def add_group_student(group_id: int, payload: GroupStudentRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.AddGroupStudent(group_student_create_to_proto(group_id, payload))
    return proto_to_dict(response)


@router.get("/group-students/{user_id}")
async def get_group_student(user_id: int, request: Request):
    response = await request.app.state.schedule_stub.GetSingleGroupStudent(schedule_service_pb2.GroupStudent(user_id=user_id))
    return proto_to_dict(response)


@router.patch("/group-students/{user_id}")
async def update_group_student(user_id: int, payload: GroupStudentUpdateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.UpdateGroupStudent(group_student_update_to_proto(user_id, payload))
    return proto_to_dict(response)


@router.delete("/group-students/{user_id}")
async def delete_group_student(user_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.DeleteGroupStudent(schedule_service_pb2.GroupStudent(user_id=user_id))
    return proto_to_dict(response)


@router.get("/items")
async def get_schedule_items(request: Request, schedule_id: int | None = None, instructor_id: int | None = None, building_id: int | None = None, room_id: int | None = None, date_from: str | None = None, date_to: str | None = None, time_slot: str | None = None, published_only: bool = False, limit: int = 100, offset: int = 0):
    grpc_request = schedule_service_pb2.AllScheduleItemsRequest(limit=limit, offset=offset)
    for field_name, value in {
        "schedule_id": schedule_id,
        "instructor_id": instructor_id,
        "building_id": building_id,
        "room_id": room_id,
        "date_from": date_from,
        "date_to": date_to,
        "time_slot": time_slot,
        "is_published": True if published_only else None,
    }.items():
        if value is not None:
            setattr(grpc_request, field_name, value)
    response = await request.app.state.schedule_stub.GetAllScheduleItems(grpc_request)
    return proto_to_dict(response)


@router.get("/items/{item_id}")
async def get_schedule_item(item_id: int, request: Request):
    response = await request.app.state.schedule_stub.GetSingleScheduleItem(schedule_service_pb2.ScheduleItem(id=item_id))
    return proto_to_dict(response)


@router.post("/items")
async def add_schedule_item(payload: ScheduleItemCreateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.AddScheduleItem(schedule_item_create_to_proto(payload))
    return proto_to_dict(response)


@router.patch("/items/{item_id}")
async def update_schedule_item(item_id: int, payload: ScheduleItemUpdateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.UpdateScheduleItem(schedule_item_update_to_proto(item_id, payload))
    return proto_to_dict(response)


@router.delete("/items/{item_id}")
async def delete_schedule_item(item_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.DeleteScheduleItem(schedule_service_pb2.ScheduleItem(id=item_id))
    return proto_to_dict(response)


@router.get("/{schedule_id}")
async def get_schedule(schedule_id: int, request: Request, user: dict = Depends(get_current_user)):
    response = await request.app.state.schedule_stub.GetSingleSchedule(
        schedule_service_pb2.Schedule(id=schedule_id)
    )
    if user.get("role") in {"student", "employee"} and not response.schedule.is_published:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Schedule is not published",
        )
    return proto_to_dict(response)


@router.patch("/{schedule_id}")
async def update_schedule(schedule_id: int, payload: ScheduleUpdateRequest, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.UpdateSchedule(schedule_update_to_proto(schedule_id, payload))
    return proto_to_dict(response)


@router.delete("/{schedule_id}")
async def delete_schedule(schedule_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.DeleteSchedule(schedule_service_pb2.Schedule(id=schedule_id))
    return proto_to_dict(response)


@router.post("/{schedule_id}/publish")
async def publish_schedule(schedule_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.PublishSchedule(schedule_service_pb2.Schedule(id=schedule_id))
    return proto_to_dict(response)


@router.post("/{schedule_id}/unpublish")
async def unpublish_schedule(schedule_id: int, request: Request, _: dict = Depends(require_roles("manager", "admin"))):
    response = await request.app.state.schedule_stub.UnpublishSchedule(schedule_service_pb2.Schedule(id=schedule_id))
    return proto_to_dict(response)

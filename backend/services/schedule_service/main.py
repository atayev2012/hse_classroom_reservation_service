from __future__ import annotations

import asyncio
import logging
import logging.config
from datetime import date
from pathlib import Path

import auth_service_pb2
import auth_service_pb2_grpc
import booking_service_pb2
import booking_service_pb2_grpc
import grpc
import schedule_service_pb2
import schedule_service_pb2_grpc

from database import async_session_maker
from service_modules.config import LOGGING_CONFIG, service_config
from service_modules.db_utils import ScheduleServiceDAO
from service_modules.models import (
    AcademicYear,
    Course,
    CourseInstructor,
    Group,
    GroupStudent,
    Holiday,
    Module,
    Programme,
    Schedule,
    ScheduleItem,
)

Path("logs").mkdir(exist_ok=True)
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("schedule_microservice")


class BookingClient:
    def __init__(self, target: str):
        self.channel = grpc.aio.insecure_channel(target)
        self.stub = booking_service_pb2_grpc.BookingServiceStub(self.channel)

    async def register_schedule_item(self, schedule: Schedule, item: ScheduleItem) -> int:
        schedule_item_marker = f"Published from schedule:{schedule.id}; item:{item.id};"
        event_description = (
            f"{schedule_item_marker} {schedule.name}"
        )
        if item.booking_id:
            response = await self.stub.UpdateBooking(
                booking_service_pb2.Booking(
                    id=item.booking_id,
                    event_type=item.type,
                    event_title=item.title,
                    event_description=event_description,
                    event_date=item.date.isoformat(),
                    event_time_slot=[item.time_slot],
                    user_id=item.instructor_id,
                    building_id=item.building_id,
                    room_id=item.room_id,
                    is_active=True,
                )
            )
            if response.success:
                return response.booking.id or item.booking_id

        existing_response = await self.stub.GetAllBookings(
            booking_service_pb2.AllBookingsRequest(
                room_id=item.room_id,
                event_date=item.date.isoformat(),
            )
        )

        if not existing_response.success:
            raise RuntimeError(existing_response.status)

        for booking in existing_response.bookings:
            if item.time_slot not in booking.event_time_slot or booking.is_active is False:
                continue
            if (
                (item.booking_id and booking.id == item.booking_id)
                or booking.event_description.startswith(schedule_item_marker)
            ):
                response = await self.stub.UpdateBooking(
                    booking_service_pb2.Booking(
                        id=booking.id,
                        event_type=item.type,
                        event_title=item.title,
                        event_description=event_description,
                        event_date=item.date.isoformat(),
                        event_time_slot=[item.time_slot],
                        user_id=item.instructor_id,
                        building_id=item.building_id,
                        room_id=item.room_id,
                        is_active=True,
                    )
                )
                if not response.success:
                    raise RuntimeError(response.status)
                return response.booking.id or booking.id
            raise RuntimeError(
                f"Room {item.room_number} is already booked on "
                f"{item.date.isoformat()} at {item.time_slot}"
            )

        response = await self.stub.AddBooking(
            booking_service_pb2.Booking(
                event_type=item.type,
                event_title=item.title,
                event_description=event_description,
                event_date=item.date.isoformat(),
                event_time_slot=[item.time_slot],
                user_id=item.instructor_id,
                building_id=item.building_id,
                room_id=item.room_id,
            )
        )

        if not response.success:
            raise RuntimeError(response.status)

        return response.booking.id

    async def delete_schedule_booking(self, booking_id: int | None) -> None:
        if not booking_id:
            return

        response = await self.stub.DeleteBooking(
            booking_service_pb2.Booking(id=booking_id)
        )
        if not response.success:
            logger.info("Schedule booking %s was not deleted: %s", booking_id, response.status)

    async def has_room_booking_conflict(
        self,
        item_date: date,
        time_slot: str,
        room_id: int,
        ignore_booking_id: int | None = None,
    ) -> bool:
        response = await self.stub.GetAllBookings(
            booking_service_pb2.AllBookingsRequest(
                room_id=room_id,
                event_date=item_date.isoformat(),
            )
        )

        if not response.success:
            raise RuntimeError(response.status)

        return any(
            booking.is_active is not False
            and time_slot in booking.event_time_slot
            and (ignore_booking_id is None or booking.id != ignore_booking_id)
            for booking in response.bookings
        )

    async def close(self) -> None:
        await self.channel.close()


class AuthClient:
    def __init__(self, target: str):
        self.channel = grpc.aio.insecure_channel(target)
        self.stub = auth_service_pb2_grpc.AuthServiceStub(self.channel)

    async def update_student_group(self, user_id: int, group_name: str) -> None:
        response = await self.stub.UpdateUser(
            auth_service_pb2.User(
                id=user_id,
                student_profile=auth_service_pb2.StudentProfile(
                    user_id=user_id,
                    group_name=group_name,
                ),
            )
        )

        if not response.success:
            raise RuntimeError(response.status)

    async def close(self) -> None:
        await self.channel.close()


class ScheduleService(schedule_service_pb2_grpc.ScheduleServiceServicer):
    def __init__(
        self,
        session_factory=async_session_maker,
        booking_client: BookingClient | None = None,
        auth_client: AuthClient | None = None,
    ):
        self.session_factory = session_factory
        self.booking_client = booking_client
        self.auth_client = auth_client
        self._background_tasks: set[asyncio.Task] = set()

    async def HealthCheck(self, request, context):
        try:
            return schedule_service_pb2.HealthCheckResponse(
                success=True,
                status="SERVING",
            )
        except asyncio.TimeoutError:
            logger.exception("Schedule service health check timed out")
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Health check timed out")
            return schedule_service_pb2.HealthCheckResponse(
                success=False,
                status="TIMEOUT",
            )
        except Exception as exc:
            logger.exception("Schedule service health check failed")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(str(exc))
            return schedule_service_pb2.HealthCheckResponse(
                success=False,
                status="UNAVAILABLE",
            )

    async def AddAcademicYear(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            academic_year = await dao.academic_years.create_academic_year(
                name=request.name,
                start_date=_parse_date(request.start_date),
                end_date=_parse_date(request.end_date),
            )

        return _academic_year_response(True, "Created", academic_year)

    async def UpdateAcademicYear(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            academic_year = await dao.academic_years.update_academic_year(
                academic_year_id=request.id,
                name=_optional_value(request, "name"),
                start_date=_optional_date(request, "start_date"),
                end_date=_optional_date(request, "end_date"),
            )

        return _academic_year_response(
            academic_year is not None,
            "Updated" if academic_year else "Academic year not found",
            academic_year,
        )

    async def DeleteAcademicYear(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            success = await dao.academic_years.delete_academic_year(request.id)

        return _academic_year_response(
            success,
            "Deleted" if success else "Academic year not found",
        )

    async def GetSingleAcademicYear(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            academic_year = await dao.academic_years.get_academic_year_by_id(
                request.id,
                load_full=True,
            )

        return _academic_year_response(
            academic_year is not None,
            "OK" if academic_year else "Academic year not found",
            academic_year,
        )

    async def GetAllAcademicYears(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            academic_years = await dao.academic_years.get_academic_years(
                limit=_limit(request),
                offset=_offset(request),
                load_modules=True,
                load_holidays=True,
            )

        return schedule_service_pb2.AllAcademicYearsResponse(
            success=True,
            status="OK",
            academic_years=[
                _academic_year_to_proto(academic_year)
                for academic_year in academic_years
            ],
        )

    async def AddModule(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            module = await dao.modules.create_module(
                name=request.name,
                start_date=_parse_date(request.start_date),
                end_date=_parse_date(request.end_date),
                academic_year_id=request.academic_year_id,
            )

        return _module_response(True, "Created", module)

    async def UpdateModule(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            module = await dao.modules.update_module(
                module_id=request.id,
                name=_optional_value(request, "name"),
                start_date=_optional_date(request, "start_date"),
                end_date=_optional_date(request, "end_date"),
                academic_year_id=_optional_value(request, "academic_year_id"),
            )

        return _module_response(
            module is not None,
            "Updated" if module else "Module not found",
            module,
        )

    async def DeleteModule(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            success = await dao.modules.delete_module(request.id)

        return _module_response(success, "Deleted" if success else "Module not found")

    async def GetSingleModule(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            module = await dao.modules.get_module_by_id(
                request.id,
                load_schedules=True,
            )

        return _module_response(
            module is not None,
            "OK" if module else "Module not found",
            module,
        )

    async def GetAllModules(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            modules = await dao.modules.get_modules(
                academic_year_id=_optional_value(request, "academic_year_id"),
                active_on=_optional_date(request, "active_on"),
                limit=_limit(request),
                offset=_offset(request),
                load_schedules=True,
            )

        return schedule_service_pb2.AllModulesResponse(
            success=True,
            status="OK",
            modules=[_module_to_proto(module) for module in modules],
        )

    async def AddHoliday(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            holiday = await dao.holidays.create_holiday(
                holiday_date=_parse_date(request.date),
                academic_year_id=request.academic_year_id,
                name=_optional_value(request, "name"),
                description=_optional_value(request, "description"),
            )

        return _holiday_response(True, "Created", holiday)

    async def UpdateHoliday(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            holiday = await dao.holidays.update_holiday(
                holiday_id=request.id,
                holiday_date=_optional_date(request, "date"),
                name=_optional_value(request, "name"),
                description=_optional_value(request, "description"),
                academic_year_id=_optional_value(request, "academic_year_id"),
            )

        return _holiday_response(
            holiday is not None,
            "Updated" if holiday else "Holiday not found",
            holiday,
        )

    async def DeleteHoliday(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            success = await dao.holidays.delete_holiday(request.id)

        return _holiday_response(success, "Deleted" if success else "Holiday not found")

    async def GetSingleHoliday(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            holiday = await dao.holidays.get_holiday_by_id(request.id)

        return _holiday_response(
            holiday is not None,
            "OK" if holiday else "Holiday not found",
            holiday,
        )

    async def GetAllHolidays(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            holidays = await dao.holidays.get_holidays(
                academic_year_id=_optional_value(request, "academic_year_id"),
                date_from=_optional_date(request, "date_from"),
                date_to=_optional_date(request, "date_to"),
                limit=_limit(request),
                offset=_offset(request),
            )

        return schedule_service_pb2.AllHolidaysResponse(
            success=True,
            status="OK",
            holidays=[_holiday_to_proto(holiday) for holiday in holidays],
        )

    async def AddProgramme(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            programme = await dao.programmes.create_programme(
                name=request.name,
                description=_optional_value(request, "description"),
            )

        return _programme_response(True, "Created", programme)

    async def UpdateProgramme(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            programme = await dao.programmes.update_programme(
                programme_id=request.id,
                name=_optional_value(request, "name"),
                description=_optional_value(request, "description"),
            )

        return _programme_response(
            programme is not None,
            "Updated" if programme else "Programme not found",
            programme,
        )

    async def DeleteProgramme(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            success = await dao.programmes.delete_programme(request.id)

        return _programme_response(
            success,
            "Deleted" if success else "Programme not found",
        )

    async def GetSingleProgramme(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            programme = await dao.programmes.get_programme_by_id(
                request.id,
                load_groups=True,
            )

        return _programme_response(
            programme is not None,
            "OK" if programme else "Programme not found",
            programme,
        )

    async def GetAllProgrammes(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            programmes = await dao.programmes.get_programmes(
                limit=_limit(request),
                offset=_offset(request),
                load_groups=True,
            )

        return schedule_service_pb2.AllProgrammesResponse(
            success=True,
            status="OK",
            programmes=[
                _programme_to_proto(programme)
                for programme in programmes
            ],
        )

    async def AddCourse(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            course = await dao.courses.create_course(
                name=request.name,
                description=_optional_value(request, "description"),
                programme_id=request.programme_id,
                instructors=[
                    {
                        "instructor_id": instructor.instructor_id,
                        "instructor_name": instructor.instructor_name,
                    }
                    for instructor in request.instructors
                ],
            )

        return _course_response(True, "Created", course)

    async def UpdateCourse(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            course = await dao.courses.update_course(
                course_id=request.id,
                name=_optional_value(request, "name"),
                description=_optional_value(request, "description"),
                programme_id=_optional_value(request, "programme_id"),
                instructors=[
                    {
                        "instructor_id": instructor.instructor_id,
                        "instructor_name": instructor.instructor_name,
                    }
                    for instructor in request.instructors
                ] if request.instructors else None,
            )

        return _course_response(
            course is not None,
            "Updated" if course else "Course not found",
            course,
        )

    async def DeleteCourse(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            success = await dao.courses.delete_course(request.id)

        return _course_response(success, "Deleted" if success else "Course not found")

    async def GetSingleCourse(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            course = await dao.courses.get_course_by_id(request.id, load_instructors=True)

        return _course_response(
            course is not None,
            "OK" if course else "Course not found",
            course,
        )

    async def GetAllCourses(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            courses = await dao.courses.get_courses(
                programme_id=_optional_value(request, "programme_id"),
                instructor_id=_optional_value(request, "instructor_id"),
                limit=_limit(request),
                offset=_offset(request),
                load_instructors=True,
            )

        return schedule_service_pb2.AllCoursesResponse(
            success=True,
            status="OK",
            courses=[_course_to_proto(course) for course in courses],
        )

    async def AddGroup(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            group = await dao.groups.create_group(
                name=request.name,
                email=request.email,
                programme_id=request.programme_id,
            )
            for student_request in request.students:
                await dao.group_students.create_group_student(
                    user_id=student_request.user_id,
                    user_email=student_request.user_email,
                    group_id=group.id,
                )
            group = await dao.groups.get_group_by_id(group.id, load_students=True)

        if group is not None:
            for student in group.__dict__.get("students", []):
                self._schedule_background_call(
                    "auth student group update",
                    self.auth_client.update_student_group(student.user_id, group.name)
                    if self.auth_client
                    else None,
                )

        return _group_response(True, "Created", group)

    async def UpdateGroup(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            group = await dao.groups.update_group(
                group_id=request.id,
                name=_optional_value(request, "name"),
                email=_optional_value(request, "email"),
                programme_id=_optional_value(request, "programme_id"),
            )

        return _group_response(
            group is not None,
            "Updated" if group else "Group not found",
            group,
        )

    async def DeleteGroup(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            success = await dao.groups.delete_group(request.id)

        return _group_response(success, "Deleted" if success else "Group not found")

    async def GetSingleGroup(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            group = await dao.groups.get_group_by_id(request.id, load_full=True)

        return _group_response(group is not None, "OK" if group else "Group not found", group)

    async def GetAllGroups(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            groups = await dao.groups.get_groups(
                programme_id=_optional_value(request, "programme_id"),
                limit=_limit(request),
                offset=_offset(request),
                load_students=True,
                load_schedules=True,
            )

        return schedule_service_pb2.AllGroupsResponse(
            success=True,
            status="OK",
            groups=[_group_to_proto(group) for group in groups],
        )

    async def AddGroupStudent(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            student = await dao.group_students.create_group_student(
                user_id=request.user_id,
                user_email=request.user_email,
                group_id=request.group_id,
            )
            group = await dao.groups.get_group_by_id(student.group_id)

        if group is not None:
            self._schedule_background_call(
                "auth student group update",
                self.auth_client.update_student_group(student.user_id, group.name)
                if self.auth_client
                else None,
            )

        return _group_student_response(True, "Created", student)

    async def UpdateGroupStudent(self, request, context):
        if not _has_field(request, "user_id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            student = await dao.group_students.update_group_student(
                user_id=request.user_id,
                user_email=_optional_value(request, "user_email"),
                group_id=_optional_value(request, "group_id"),
            )
            group = (
                await dao.groups.get_group_by_id(student.group_id)
                if student is not None
                else None
            )

        if student is not None and group is not None:
            self._schedule_background_call(
                "auth student group update",
                self.auth_client.update_student_group(student.user_id, group.name)
                if self.auth_client
                else None,
            )

        return _group_student_response(
            student is not None,
            "Updated" if student else "Student not found",
            student,
        )

    async def DeleteGroupStudent(self, request, context):
        if not _has_field(request, "user_id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            success = await dao.group_students.delete_group_student(request.user_id)

        return _group_student_response(
            success,
            "Deleted" if success else "Student not found",
        )

    async def GetSingleGroupStudent(self, request, context):
        if not _has_field(request, "user_id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "user_id is required")

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            student = await dao.group_students.get_by_user_id(request.user_id)

        return _group_student_response(
            student is not None,
            "OK" if student else "Student not found",
            student,
        )

    async def GetAllGroupStudents(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            students = await dao.group_students.get_students_by_group(
                group_id=request.group_id,
                limit=_limit(request),
                offset=_offset(request),
            )

        return schedule_service_pb2.AllGroupStudentsResponse(
            success=True,
            status="OK",
            students=[_group_student_to_proto(student) for student in students],
        )

    async def AddSchedule(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            schedule = await dao.schedules.create_schedule(
                name=request.name,
                module_id=request.module_id,
                group_id=request.group_id,
                is_published=False,
            )

        return _schedule_response(True, "Created", schedule)

    async def UpdateSchedule(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            schedule = await dao.schedules.update_schedule(
                schedule_id=request.id,
                name=_optional_value(request, "name"),
                module_id=_optional_value(request, "module_id"),
                group_id=_optional_value(request, "group_id"),
                is_published=_optional_value(request, "is_published"),
            )

        return _schedule_response(
            schedule is not None,
            "Updated" if schedule else "Schedule not found",
            schedule,
        )

    async def DeleteSchedule(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            schedule = await dao.schedules.get_schedule_by_id(
                request.id,
                load_items=True,
            )
            booking_ids = [
                item.booking_id
                for item in schedule.__dict__.get("schedule_items", [])
                if item.booking_id
            ] if schedule is not None else []
            success = await dao.schedules.delete_schedule(request.id)

        if success and self.booking_client is not None:
            for booking_id in booking_ids:
                await self.booking_client.delete_schedule_booking(booking_id)

        return _schedule_response(success, "Deleted" if success else "Schedule not found")

    async def GetSingleSchedule(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            schedule = await dao.schedules.get_schedule_by_id(
                request.id,
                load_full=True,
            )

        return _schedule_response(
            schedule is not None,
            "OK" if schedule else "Schedule not found",
            schedule,
        )

    async def GetAllSchedules(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            schedules = await dao.schedules.get_schedules(
                module_id=_optional_value(request, "module_id"),
                group_id=_optional_value(request, "group_id"),
                is_published=_optional_value(request, "is_published"),
                limit=_limit(request),
                offset=_offset(request),
                load_items=True,
            )

        return schedule_service_pb2.AllSchedulesResponse(
            success=True,
            status="OK",
            schedules=[_schedule_to_proto(schedule) for schedule in schedules],
        )

    async def AddScheduleItem(self, request, context):
        item_date = _parse_date(request.date)
        has_booking_conflict = False
        if self.booking_client is not None:
            try:
                has_booking_conflict = await self.booking_client.has_room_booking_conflict(
                    item_date=item_date,
                    time_slot=request.time_slot,
                    room_id=request.room_id,
                    ignore_booking_id=_optional_value(request, "booking_id"),
                )
            except Exception:
                logger.exception("Failed to verify booking conflict for schedule item")

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            item = await dao.schedule_items.create_schedule_item(
                title=request.title,
                item_type=request.item_type,
                instructor_id=request.instructor_id,
                instructor_name=request.instructor_name,
                building_id=request.building_id,
                building_address=request.building_address,
                room_id=request.room_id,
                room_number=request.room_number,
                item_date=item_date,
                time_slot=request.time_slot,
                schedule_id=request.schedule_id,
                booking_id=_optional_value(request, "booking_id"),
                course_id=_optional_value(request, "course_id"),
            )
            await dao.schedules.set_published(request.schedule_id, False)

        return _schedule_item_response(
            True,
            "Created with booking conflict" if has_booking_conflict else "Created",
            item,
        )

    async def UpdateScheduleItem(self, request, context):
        _require_id(request, context)
        requested_date = _optional_date(request, "date")
        requested_time_slot = _optional_value(request, "time_slot")
        requested_room_id = _optional_value(request, "room_id")
        has_booking_conflict = False

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            current_item = await dao.schedule_items.get_schedule_item_by_id(request.id)
            if (
                current_item is not None
                and self.booking_client is not None
            ):
                item_date = requested_date or current_item.date
                time_slot = requested_time_slot or current_item.time_slot
                room_id = requested_room_id or current_item.room_id
                try:
                    has_booking_conflict = await self.booking_client.has_room_booking_conflict(
                        item_date=item_date,
                        time_slot=time_slot,
                        room_id=room_id,
                        ignore_booking_id=current_item.booking_id,
                    )
                except Exception:
                    logger.exception("Failed to verify booking conflict for schedule item")
            item = await dao.schedule_items.update_schedule_item(
                schedule_item_id=request.id,
                title=_optional_value(request, "title"),
                item_type=_optional_value(request, "item_type"),
                instructor_id=_optional_value(request, "instructor_id"),
                instructor_name=_optional_value(request, "instructor_name"),
                building_id=_optional_value(request, "building_id"),
                building_address=_optional_value(request, "building_address"),
                room_id=_optional_value(request, "room_id"),
                room_number=_optional_value(request, "room_number"),
                item_date=requested_date,
                time_slot=requested_time_slot,
                schedule_id=_optional_value(request, "schedule_id"),
                booking_id=_optional_value(request, "booking_id"),
                course_id=_optional_value(request, "course_id"),
            )
            if item is not None:
                await dao.schedules.set_published(item.schedule_id, False)

        if item is not None and item.booking_id and self.booking_client is not None:
            try:
                async with self.session_factory() as session:
                    dao = ScheduleServiceDAO(session)
                    schedule = await dao.schedules.get_schedule_by_id(item.schedule_id)
                if schedule is not None:
                    booking_id = await self.booking_client.register_schedule_item(schedule, item)
                    async with self.session_factory() as session:
                        dao = ScheduleServiceDAO(session)
                        await dao.schedule_items.set_booking_id(item.id, booking_id)
            except Exception:
                logger.exception("Failed to update represented booking for schedule item %s", item.id)

        return _schedule_item_response(
            item is not None,
            "Updated with booking conflict" if item and has_booking_conflict else "Updated" if item else "Schedule item not found",
            item,
        )

    async def DeleteScheduleItem(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            item = await dao.schedule_items.get_schedule_item_by_id(request.id)
            booking_id = item.booking_id if item is not None else None
            success = await dao.schedule_items.delete_schedule_item(request.id)
            if success and item is not None:
                await dao.schedules.set_published(item.schedule_id, False)

        if success and self.booking_client is not None:
            await self.booking_client.delete_schedule_booking(booking_id)

        return _schedule_item_response(
            success,
            "Deleted" if success else "Schedule item not found",
        )

    async def GetSingleScheduleItem(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            item = await dao.schedule_items.get_schedule_item_by_id(request.id)

        return _schedule_item_response(
            item is not None,
            "OK" if item else "Schedule item not found",
            item,
        )

    async def GetAllScheduleItems(self, request, context):
        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            items = await dao.schedule_items.get_schedule_items(
                schedule_id=_optional_value(request, "schedule_id"),
                instructor_id=_optional_value(request, "instructor_id"),
                building_id=_optional_value(request, "building_id"),
                room_id=_optional_value(request, "room_id"),
                date_from=_optional_date(request, "date_from"),
                date_to=_optional_date(request, "date_to"),
                time_slot=_optional_value(request, "time_slot"),
                is_published=_optional_value(request, "is_published"),
                limit=_limit(request),
                offset=_offset(request),
            )

        return schedule_service_pb2.AllScheduleItemsResponse(
            success=True,
            status="OK",
            schedule_items=[_schedule_item_to_proto(item) for item in items],
        )

    async def PublishSchedule(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            schedule = await dao.schedules.get_schedule_by_id(
                request.id,
                load_full=True,
            )

        if schedule is None:
            return _schedule_response(False, "Schedule not found")
        if schedule.is_published:
            return _schedule_response(True, "Already published", schedule)

        try:
            if self.booking_client is not None:
                booking_ids: dict[int, int] = {}
                for item in schedule.__dict__.get("schedule_items", []):
                    booking_ids[item.id] = await self.booking_client.register_schedule_item(schedule, item)
        except Exception as exc:
            logger.exception("Failed to register schedule %s in booking service", request.id)
            return _schedule_response(False, f"Booking registration failed: {exc}", schedule)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            if self.booking_client is not None:
                for item_id, booking_id in booking_ids.items():
                    await dao.schedule_items.set_booking_id(item_id, booking_id)
            await dao.schedules.set_published(request.id, True)
            schedule = await dao.schedules.get_schedule_by_id(
                request.id,
                load_full=True,
            )

        return _schedule_response(True, "Published", schedule)

    async def UnpublishSchedule(self, request, context):
        _require_id(request, context)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            schedule = await dao.schedules.get_schedule_by_id(
                request.id,
                load_full=True,
            )

        if schedule is None:
            return _schedule_response(False, "Schedule not found")
        if not schedule.is_published:
            return _schedule_response(True, "Already draft", schedule)

        booking_ids = [
            item.booking_id
            for item in schedule.__dict__.get("schedule_items", [])
            if item.booking_id
        ]

        if self.booking_client is not None:
            for booking_id in booking_ids:
                await self.booking_client.delete_schedule_booking(booking_id)

        async with self.session_factory() as session:
            dao = ScheduleServiceDAO(session)
            for item in schedule.__dict__.get("schedule_items", []):
                if item.booking_id:
                    await dao.schedule_items.set_booking_id(item.id, None)
            await dao.schedules.set_published(request.id, False)
            schedule = await dao.schedules.get_schedule_by_id(
                request.id,
                load_full=True,
            )

        return _schedule_response(True, "Unpublished", schedule)

    def _schedule_background_call(self, name: str, coroutine) -> None:
        if coroutine is None:
            return

        task = asyncio.create_task(coroutine)
        self._background_tasks.add(task)

        def _done_callback(done_task: asyncio.Task) -> None:
            self._background_tasks.discard(done_task)
            try:
                done_task.result()
            except Exception:
                logger.exception("Background %s call failed", name)

        task.add_done_callback(_done_callback)


def _academic_year_to_proto(academic_year: AcademicYear):
    return schedule_service_pb2.AcademicYear(
        id=academic_year.id,
        name=academic_year.name,
        start_date=academic_year.start_date.isoformat(),
        end_date=academic_year.end_date.isoformat(),
        modules=[
            _module_to_proto(module)
            for module in academic_year.__dict__.get("modules", [])
        ],
        holidays=[
            _holiday_to_proto(holiday)
            for holiday in academic_year.__dict__.get("holidays", [])
        ],
    )


def _module_to_proto(module: Module):
    return schedule_service_pb2.Module(
        id=module.id,
        name=module.name,
        start_date=module.start_date.isoformat(),
        end_date=module.end_date.isoformat(),
        academic_year_id=module.academic_year_id,
        schedules=[
            _schedule_to_proto(schedule)
            for schedule in module.__dict__.get("schedules", [])
        ],
    )


def _holiday_to_proto(holiday: Holiday):
    holiday_proto = schedule_service_pb2.Holiday(
        id=holiday.id,
        date=holiday.date.isoformat(),
        academic_year_id=holiday.academic_year_id,
    )
    if holiday.name is not None:
        holiday_proto.name = holiday.name
    if holiday.description is not None:
        holiday_proto.description = holiday.description
    return holiday_proto


def _programme_to_proto(programme: Programme):
    programme_proto = schedule_service_pb2.Programme(
        id=programme.id,
        name=programme.name,
        groups=[
            _group_to_proto(group)
            for group in programme.__dict__.get("groups", [])
        ],
        courses=[
            _course_to_proto(course)
            for course in programme.__dict__.get("courses", [])
        ],
    )
    if programme.description is not None:
        programme_proto.description = programme.description
    return programme_proto


def _course_instructor_to_proto(instructor: CourseInstructor):
    return schedule_service_pb2.CourseInstructor(
        id=instructor.id,
        course_id=instructor.course_id,
        instructor_id=instructor.instructor_id,
        instructor_name=instructor.instructor_name,
    )


def _course_to_proto(course: Course):
    course_proto = schedule_service_pb2.Course(
        id=course.id,
        name=course.name,
        programme_id=course.programme_id,
        instructors=[
            _course_instructor_to_proto(instructor)
            for instructor in course.__dict__.get("instructors", [])
        ],
    )
    if course.description is not None:
        course_proto.description = course.description
    return course_proto


def _group_to_proto(group: Group):
    return schedule_service_pb2.Group(
        id=group.id,
        name=group.name,
        email=group.email,
        programme_id=group.programme_id,
        students=[
            _group_student_to_proto(student)
            for student in group.__dict__.get("students", [])
        ],
        schedules=[
            _schedule_to_proto(schedule)
            for schedule in group.__dict__.get("schedules", [])
        ],
    )


def _group_student_to_proto(student: GroupStudent):
    return schedule_service_pb2.GroupStudent(
        user_id=student.user_id,
        user_email=student.user_email,
        group_id=student.group_id,
    )


def _schedule_to_proto(schedule: Schedule):
    return schedule_service_pb2.Schedule(
        id=schedule.id,
        name=schedule.name,
        module_id=schedule.module_id,
        group_id=schedule.group_id,
        is_published=schedule.is_published,
        schedule_items=[
            _schedule_item_to_proto(item)
            for item in schedule.__dict__.get("schedule_items", [])
        ],
    )


def _schedule_item_to_proto(item: ScheduleItem):
    proto = schedule_service_pb2.ScheduleItem(
        id=item.id,
        title=item.title,
        item_type=item.type,
        instructor_id=item.instructor_id,
        instructor_name=item.instructor_name,
        building_id=item.building_id,
        building_address=item.building_address,
        room_id=item.room_id,
        room_number=item.room_number,
        date=item.date.isoformat(),
        time_slot=item.time_slot,
        schedule_id=item.schedule_id,
    )
    if item.booking_id is not None:
        proto.booking_id = item.booking_id
    if item.course_id is not None:
        proto.course_id = item.course_id
    return proto


def _academic_year_response(success: bool, status: str, academic_year=None):
    response = schedule_service_pb2.AcademicYearResponse(success=success, status=status)
    if academic_year is not None:
        response.academic_year.CopyFrom(_academic_year_to_proto(academic_year))
    return response


def _module_response(success: bool, status: str, module=None):
    response = schedule_service_pb2.ModuleResponse(success=success, status=status)
    if module is not None:
        response.module.CopyFrom(_module_to_proto(module))
    return response


def _holiday_response(success: bool, status: str, holiday=None):
    response = schedule_service_pb2.HolidayResponse(success=success, status=status)
    if holiday is not None:
        response.holiday.CopyFrom(_holiday_to_proto(holiday))
    return response


def _programme_response(success: bool, status: str, programme=None):
    response = schedule_service_pb2.ProgrammeResponse(success=success, status=status)
    if programme is not None:
        response.programme.CopyFrom(_programme_to_proto(programme))
    return response


def _course_response(success: bool, status: str, course=None):
    response = schedule_service_pb2.CourseResponse(success=success, status=status)
    if course is not None:
        response.course.CopyFrom(_course_to_proto(course))
    return response


def _group_response(success: bool, status: str, group=None):
    response = schedule_service_pb2.GroupResponse(success=success, status=status)
    if group is not None:
        response.group.CopyFrom(_group_to_proto(group))
    return response


def _group_student_response(success: bool, status: str, student=None):
    response = schedule_service_pb2.GroupStudentResponse(success=success, status=status)
    if student is not None:
        response.student.CopyFrom(_group_student_to_proto(student))
    return response


def _schedule_response(success: bool, status: str, schedule=None):
    response = schedule_service_pb2.ScheduleResponse(success=success, status=status)
    if schedule is not None:
        response.schedule.CopyFrom(_schedule_to_proto(schedule))
    return response


def _schedule_item_response(success: bool, status: str, item=None):
    response = schedule_service_pb2.ScheduleItemResponse(success=success, status=status)
    if item is not None:
        response.schedule_item.CopyFrom(_schedule_item_to_proto(item))
    return response


def _has_field(message, field_name: str) -> bool:
    try:
        return message.HasField(field_name)
    except ValueError:
        return bool(getattr(message, field_name))


def _optional_value(message, field_name: str, default=None):
    return getattr(message, field_name) if _has_field(message, field_name) else default


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _optional_date(message, field_name: str) -> date | None:
    return _parse_date(getattr(message, field_name)) if _has_field(message, field_name) else None


def _limit(request) -> int:
    return request.limit if _has_field(request, "limit") else 100


def _offset(request) -> int:
    return request.offset if _has_field(request, "offset") else 0


def _require_id(request, context) -> None:
    if not _has_field(request, "id"):
        raise grpc.RpcError("id is required")


async def serve() -> None:
    server = grpc.aio.server()
    booking_client = BookingClient(
        f"{service_config.BOOKING_SERVICE_HOST}:{service_config.BOOKING_SERVICE_PORT}"
    )
    auth_client = AuthClient(
        f"{service_config.AUTH_SERVICE_HOST}:{service_config.AUTH_SERVICE_PORT}"
    )
    schedule_service_pb2_grpc.add_ScheduleServiceServicer_to_server(
        ScheduleService(
            booking_client=booking_client,
            auth_client=auth_client,
        ),
        server,
    )

    listen_addr = f"{service_config.HOST}:{service_config.PORT}"
    server.add_insecure_port(listen_addr)

    await server.start()
    logger.info("Schedule service started at %s", listen_addr)
    try:
        await server.wait_for_termination()
    finally:
        await booking_client.close()
        await auth_client.close()


if __name__ == "__main__":
    asyncio.run(serve())

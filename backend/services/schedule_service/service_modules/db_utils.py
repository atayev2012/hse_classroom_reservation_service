from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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

ModelType = TypeVar("ModelType")


class BaseDAO(Generic[ModelType]):
    model: type[ModelType]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **data: Any) -> ModelType:
        instance = self.model(**data)

        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)

        return instance

    async def get_by_id(self, object_id: int) -> ModelType | None:
        return await self.session.get(self.model, object_id)

    async def get_one_or_none(self, **filters: Any) -> ModelType | None:
        stmt = select(self.model).filter_by(**filters)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        **filters: Any,
    ) -> Sequence[ModelType]:
        stmt = (
            select(self.model)
            .filter_by(**filters)
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_by_id(self, object_id: int, **data: Any) -> ModelType | None:
        instance = await self.get_by_id(object_id)

        if instance is None:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(instance, key, value)

        await self.session.commit()
        await self.session.refresh(instance)

        return instance

    async def delete_by_id(self, object_id: int) -> bool:
        instance = await self.get_by_id(object_id)

        if instance is None:
            return False

        await self.session.delete(instance)
        await self.session.commit()

        return True

    async def exists(self, **filters: Any) -> bool:
        stmt = select(self.model).filter_by(**filters).limit(1)

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)

        result = await self.session.execute(stmt)
        return result.scalar_one()


class AcademicYearDAO(BaseDAO[AcademicYear]):
    model = AcademicYear

    @staticmethod
    def _load_modules():
        return selectinload(AcademicYear.modules)

    @staticmethod
    def _load_holidays():
        return selectinload(AcademicYear.holidays)

    @staticmethod
    def _load_full():
        return (
            selectinload(AcademicYear.modules).selectinload(Module.schedules),
            selectinload(AcademicYear.holidays),
        )

    async def create_academic_year(
        self,
        name: str,
        start_date: date,
        end_date: date,
    ) -> AcademicYear:
        return await self.create(
            name=name,
            start_date=start_date,
            end_date=end_date,
        )

    async def get_academic_year_by_id(
        self,
        academic_year_id: int,
        load_modules: bool = False,
        load_holidays: bool = False,
        load_full: bool = False,
    ) -> AcademicYear | None:
        stmt = select(AcademicYear).where(AcademicYear.id == academic_year_id)

        if load_full:
            stmt = stmt.options(*self._load_full())
        else:
            if load_modules:
                stmt = stmt.options(self._load_modules())
            if load_holidays:
                stmt = stmt.options(self._load_holidays())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_academic_year_by_name(
        self,
        name: str,
        load_full: bool = False,
    ) -> AcademicYear | None:
        stmt = select(AcademicYear).where(AcademicYear.name == name)

        if load_full:
            stmt = stmt.options(*self._load_full())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_academic_years(
        self,
        limit: int = 100,
        offset: int = 0,
        load_modules: bool = False,
        load_holidays: bool = False,
    ) -> Sequence[AcademicYear]:
        stmt = select(AcademicYear).limit(limit).offset(offset)

        if load_modules:
            stmt = stmt.options(self._load_modules())
        if load_holidays:
            stmt = stmt.options(self._load_holidays())

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_academic_year(
        self,
        academic_year_id: int,
        name: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> AcademicYear | None:
        return await self.update_by_id(
            academic_year_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
        )

    async def delete_academic_year(self, academic_year_id: int) -> bool:
        return await self.delete_by_id(academic_year_id)


class ModuleDAO(BaseDAO[Module]):
    model = Module

    @staticmethod
    def _load_academic_year():
        return selectinload(Module.academic_year)

    @staticmethod
    def _load_schedules():
        return selectinload(Module.schedules)

    async def create_module(
        self,
        name: str,
        start_date: date,
        end_date: date,
        academic_year_id: int,
    ) -> Module:
        return await self.create(
            name=name,
            start_date=start_date,
            end_date=end_date,
            academic_year_id=academic_year_id,
        )

    async def get_module_by_id(
        self,
        module_id: int,
        load_academic_year: bool = False,
        load_schedules: bool = False,
    ) -> Module | None:
        stmt = select(Module).where(Module.id == module_id)

        if load_academic_year:
            stmt = stmt.options(self._load_academic_year())
        if load_schedules:
            stmt = stmt.options(self._load_schedules())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_modules(
        self,
        academic_year_id: int | None = None,
        active_on: date | None = None,
        limit: int = 100,
        offset: int = 0,
        load_academic_year: bool = False,
        load_schedules: bool = False,
    ) -> Sequence[Module]:
        stmt = select(Module)

        if academic_year_id is not None:
            stmt = stmt.where(Module.academic_year_id == academic_year_id)
        if active_on is not None:
            stmt = stmt.where(
                Module.start_date <= active_on,
                Module.end_date >= active_on,
            )
        if load_academic_year:
            stmt = stmt.options(self._load_academic_year())
        if load_schedules:
            stmt = stmt.options(self._load_schedules())

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_module(
        self,
        module_id: int,
        name: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        academic_year_id: int | None = None,
    ) -> Module | None:
        return await self.update_by_id(
            module_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            academic_year_id=academic_year_id,
        )

    async def delete_module(self, module_id: int) -> bool:
        return await self.delete_by_id(module_id)


class HolidayDAO(BaseDAO[Holiday]):
    model = Holiday

    async def create_holiday(
        self,
        holiday_date: date,
        academic_year_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> Holiday:
        return await self.create(
            date=holiday_date,
            name=name,
            description=description,
            academic_year_id=academic_year_id,
        )

    async def get_holiday_by_id(
        self,
        holiday_id: int,
        load_academic_year: bool = False,
    ) -> Holiday | None:
        stmt = select(Holiday).where(Holiday.id == holiday_id)

        if load_academic_year:
            stmt = stmt.options(selectinload(Holiday.academic_year))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_holidays(
        self,
        academic_year_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        limit: int = 100,
        offset: int = 0,
        load_academic_year: bool = False,
    ) -> Sequence[Holiday]:
        stmt = select(Holiday)

        if academic_year_id is not None:
            stmt = stmt.where(Holiday.academic_year_id == academic_year_id)
        if date_from is not None:
            stmt = stmt.where(Holiday.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(Holiday.date <= date_to)
        if load_academic_year:
            stmt = stmt.options(selectinload(Holiday.academic_year))

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_holiday(
        self,
        holiday_id: int,
        holiday_date: date | None = None,
        name: str | None = None,
        description: str | None = None,
        academic_year_id: int | None = None,
    ) -> Holiday | None:
        data: dict[str, Any] = {
            "name": name,
            "description": description,
            "academic_year_id": academic_year_id,
        }

        if holiday_date is not None:
            data["date"] = holiday_date

        return await self.update_by_id(holiday_id, **data)

    async def delete_holiday(self, holiday_id: int) -> bool:
        return await self.delete_by_id(holiday_id)


class ProgrammeDAO(BaseDAO[Programme]):
    model = Programme

    async def create_programme(
        self,
        name: str,
        description: str | None = None,
    ) -> Programme:
        return await self.create(name=name, description=description)

    async def get_programme_by_id(
        self,
        programme_id: int,
        load_groups: bool = False,
    ) -> Programme | None:
        stmt = select(Programme).where(Programme.id == programme_id)

        if load_groups:
            stmt = stmt.options(selectinload(Programme.groups))
            stmt = stmt.options(selectinload(Programme.courses).selectinload(Course.instructors))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_programme_by_name(
        self,
        name: str,
        load_groups: bool = False,
    ) -> Programme | None:
        stmt = select(Programme).where(Programme.name == name)

        if load_groups:
            stmt = stmt.options(selectinload(Programme.groups))
            stmt = stmt.options(selectinload(Programme.courses).selectinload(Course.instructors))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_programmes(
        self,
        limit: int = 100,
        offset: int = 0,
        load_groups: bool = False,
    ) -> Sequence[Programme]:
        stmt = select(Programme).limit(limit).offset(offset)

        if load_groups:
            stmt = stmt.options(selectinload(Programme.groups))
            stmt = stmt.options(selectinload(Programme.courses).selectinload(Course.instructors))

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_programme(
        self,
        programme_id: int,
        name: str | None = None,
        description: str | None = None,
    ) -> Programme | None:
        return await self.update_by_id(
            programme_id,
            name=name,
            description=description,
        )

    async def delete_programme(self, programme_id: int) -> bool:
        return await self.delete_by_id(programme_id)


class CourseDAO(BaseDAO[Course]):
    model = Course

    async def create_course(
        self,
        name: str,
        programme_id: int,
        description: str | None = None,
        instructors: Sequence[dict[str, Any]] | None = None,
    ) -> Course:
        course = Course(
            name=name,
            description=description,
            programme_id=programme_id,
        )
        course.instructors = [
            CourseInstructor(
                instructor_id=int(instructor["instructor_id"]),
                instructor_name=str(instructor["instructor_name"]),
            )
            for instructor in instructors or []
        ]
        self.session.add(course)
        await self.session.commit()
        await self.session.refresh(course)
        return await self.get_course_by_id(course.id, load_instructors=True) or course

    async def get_course_by_id(
        self,
        course_id: int,
        load_instructors: bool = False,
        load_programme: bool = False,
    ) -> Course | None:
        stmt = select(Course).where(Course.id == course_id)

        if load_instructors:
            stmt = stmt.options(selectinload(Course.instructors))
        if load_programme:
            stmt = stmt.options(selectinload(Course.programme))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_courses(
        self,
        programme_id: int | None = None,
        instructor_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
        load_instructors: bool = False,
    ) -> Sequence[Course]:
        stmt = select(Course)

        if programme_id is not None:
            stmt = stmt.where(Course.programme_id == programme_id)
        if instructor_id is not None:
            stmt = stmt.join(CourseInstructor).where(CourseInstructor.instructor_id == instructor_id)
        if load_instructors:
            stmt = stmt.options(selectinload(Course.instructors))

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().unique().all()

    async def update_course(
        self,
        course_id: int,
        name: str | None = None,
        description: str | None = None,
        programme_id: int | None = None,
        instructors: Sequence[dict[str, Any]] | None = None,
    ) -> Course | None:
        course = await self.get_course_by_id(course_id, load_instructors=True)

        if course is None:
            return None

        if name is not None:
            course.name = name
        if description is not None:
            course.description = description
        if programme_id is not None:
            course.programme_id = programme_id
        if instructors is not None:
            course.instructors = [
                CourseInstructor(
                    instructor_id=int(instructor["instructor_id"]),
                    instructor_name=str(instructor["instructor_name"]),
                )
                for instructor in instructors
            ]

        await self.session.commit()
        await self.session.refresh(course)
        return await self.get_course_by_id(course.id, load_instructors=True)

    async def delete_course(self, course_id: int) -> bool:
        return await self.delete_by_id(course_id)


class CourseInstructorDAO(BaseDAO[CourseInstructor]):
    model = CourseInstructor


class GroupDAO(BaseDAO[Group]):
    model = Group

    @staticmethod
    def _load_full():
        return (
            selectinload(Group.programme),
            selectinload(Group.students),
            selectinload(Group.schedules).selectinload(Schedule.schedule_items),
        )

    async def create_group(
        self,
        name: str,
        email: str,
        programme_id: int,
    ) -> Group:
        return await self.create(
            name=name,
            email=email,
            programme_id=programme_id,
        )

    async def get_group_by_id(
        self,
        group_id: int,
        load_programme: bool = False,
        load_students: bool = False,
        load_schedules: bool = False,
        load_full: bool = False,
    ) -> Group | None:
        stmt = select(Group).where(Group.id == group_id)

        if load_full:
            stmt = stmt.options(*self._load_full())
        else:
            if load_programme:
                stmt = stmt.options(selectinload(Group.programme))
            if load_students:
                stmt = stmt.options(selectinload(Group.students))
            if load_schedules:
                stmt = stmt.options(selectinload(Group.schedules))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_group_by_email(
        self,
        email: str,
        load_full: bool = False,
    ) -> Group | None:
        stmt = select(Group).where(Group.email == email)

        if load_full:
            stmt = stmt.options(*self._load_full())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_groups(
        self,
        programme_id: int | None = None,
        limit: int = 100,
        offset: int = 0,
        load_programme: bool = False,
        load_students: bool = False,
        load_schedules: bool = False,
    ) -> Sequence[Group]:
        stmt = select(Group)

        if programme_id is not None:
            stmt = stmt.where(Group.programme_id == programme_id)
        if load_programme:
            stmt = stmt.options(selectinload(Group.programme))
        if load_students:
            stmt = stmt.options(selectinload(Group.students))
        if load_schedules:
            stmt = stmt.options(selectinload(Group.schedules))

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_group(
        self,
        group_id: int,
        name: str | None = None,
        email: str | None = None,
        programme_id: int | None = None,
    ) -> Group | None:
        return await self.update_by_id(
            group_id,
            name=name,
            email=email,
            programme_id=programme_id,
        )

    async def delete_group(self, group_id: int) -> bool:
        return await self.delete_by_id(group_id)


class GroupStudentDAO(BaseDAO[GroupStudent]):
    model = GroupStudent

    async def create_group_student(
        self,
        user_id: int,
        user_email: str,
        group_id: int,
    ) -> GroupStudent:
        return await self.create(
            user_id=user_id,
            user_email=user_email,
            group_id=group_id,
        )

    async def get_by_user_id(
        self,
        user_id: int,
        load_group: bool = False,
    ) -> GroupStudent | None:
        stmt = select(GroupStudent).where(GroupStudent.user_id == user_id)

        if load_group:
            stmt = stmt.options(selectinload(GroupStudent.group))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_students_by_group(
        self,
        group_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[GroupStudent]:
        stmt = (
            select(GroupStudent)
            .where(GroupStudent.group_id == group_id)
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_group_student(
        self,
        user_id: int,
        user_email: str | None = None,
        group_id: int | None = None,
    ) -> GroupStudent | None:
        return await self.update_by_id(
            user_id,
            user_email=user_email,
            group_id=group_id,
        )

    async def delete_group_student(self, user_id: int) -> bool:
        return await self.delete_by_id(user_id)


class ScheduleDAO(BaseDAO[Schedule]):
    model = Schedule

    @staticmethod
    def _load_full():
        return (
            selectinload(Schedule.module).selectinload(Module.academic_year),
            selectinload(Schedule.group).selectinload(Group.programme),
            selectinload(Schedule.schedule_items),
        )

    async def create_schedule(
        self,
        name: str,
        module_id: int,
        group_id: int,
        is_published: bool = False,
    ) -> Schedule:
        return await self.create(
            name=name,
            module_id=module_id,
            group_id=group_id,
            is_published=is_published,
        )

    async def get_schedule_by_id(
        self,
        schedule_id: int,
        load_module: bool = False,
        load_group: bool = False,
        load_items: bool = False,
        load_full: bool = False,
    ) -> Schedule | None:
        stmt = select(Schedule).where(Schedule.id == schedule_id)

        if load_full:
            stmt = stmt.options(*self._load_full())
        else:
            if load_module:
                stmt = stmt.options(selectinload(Schedule.module))
            if load_group:
                stmt = stmt.options(selectinload(Schedule.group))
            if load_items:
                stmt = stmt.options(selectinload(Schedule.schedule_items))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_schedules(
        self,
        module_id: int | None = None,
        group_id: int | None = None,
        is_published: bool | None = None,
        limit: int = 100,
        offset: int = 0,
        load_module: bool = False,
        load_group: bool = False,
        load_items: bool = False,
    ) -> Sequence[Schedule]:
        stmt = select(Schedule)

        if module_id is not None:
            stmt = stmt.where(Schedule.module_id == module_id)
        if group_id is not None:
            stmt = stmt.where(Schedule.group_id == group_id)
        if is_published is not None:
            stmt = stmt.where(Schedule.is_published == is_published)
        if load_module:
            stmt = stmt.options(selectinload(Schedule.module))
        if load_group:
            stmt = stmt.options(selectinload(Schedule.group))
        if load_items:
            stmt = stmt.options(selectinload(Schedule.schedule_items))

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_schedule(
        self,
        schedule_id: int,
        name: str | None = None,
        module_id: int | None = None,
        group_id: int | None = None,
        is_published: bool | None = None,
    ) -> Schedule | None:
        return await self.update_by_id(
            schedule_id,
            name=name,
            module_id=module_id,
            group_id=group_id,
            is_published=is_published,
        )

    async def set_published(
        self,
        schedule_id: int,
        is_published: bool,
    ) -> Schedule | None:
        return await self.update_schedule(
            schedule_id=schedule_id,
            is_published=is_published,
        )

    async def delete_schedule(self, schedule_id: int) -> bool:
        return await self.delete_by_id(schedule_id)


class ScheduleItemDAO(BaseDAO[ScheduleItem]):
    model = ScheduleItem

    async def create_schedule_item(
        self,
        title: str,
        item_type: str,
        instructor_id: int,
        instructor_name: str,
        building_id: int,
        building_address: str,
        room_id: int,
        room_number: str,
        item_date: date,
        time_slot: str,
        schedule_id: int,
        booking_id: int | None = None,
        course_id: int | None = None,
    ) -> ScheduleItem:
        return await self.create(
            title=title,
            type=item_type,
            instructor_id=instructor_id,
            instructor_name=instructor_name,
            building_id=building_id,
            building_address=building_address,
            room_id=room_id,
            room_number=room_number,
            date=item_date,
            time_slot=time_slot,
            schedule_id=schedule_id,
            booking_id=booking_id,
            course_id=course_id,
        )

    async def get_schedule_item_by_id(
        self,
        schedule_item_id: int,
        load_schedule: bool = False,
    ) -> ScheduleItem | None:
        stmt = select(ScheduleItem).where(ScheduleItem.id == schedule_item_id)

        if load_schedule:
            stmt = stmt.options(selectinload(ScheduleItem.schedule))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_schedule_items(
        self,
        schedule_id: int | None = None,
        instructor_id: int | None = None,
        building_id: int | None = None,
        room_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        time_slot: str | None = None,
        is_published: bool | None = None,
        limit: int = 100,
        offset: int = 0,
        load_schedule: bool = False,
        load_course: bool = False,
    ) -> Sequence[ScheduleItem]:
        stmt = select(ScheduleItem)

        if is_published is not None:
            stmt = stmt.join(Schedule).where(Schedule.is_published == is_published)
        if schedule_id is not None:
            stmt = stmt.where(ScheduleItem.schedule_id == schedule_id)
        if instructor_id is not None:
            stmt = stmt.where(ScheduleItem.instructor_id == instructor_id)
        if building_id is not None:
            stmt = stmt.where(ScheduleItem.building_id == building_id)
        if room_id is not None:
            stmt = stmt.where(ScheduleItem.room_id == room_id)
        if date_from is not None:
            stmt = stmt.where(ScheduleItem.date >= date_from)
        if date_to is not None:
            stmt = stmt.where(ScheduleItem.date <= date_to)
        if time_slot is not None:
            stmt = stmt.where(ScheduleItem.time_slot == time_slot)
        if load_schedule:
            stmt = stmt.options(selectinload(ScheduleItem.schedule))
        if load_course:
            stmt = stmt.options(selectinload(ScheduleItem.course).selectinload(Course.instructors))

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_schedule_item(
        self,
        schedule_item_id: int,
        title: str | None = None,
        item_type: str | None = None,
        instructor_id: int | None = None,
        instructor_name: str | None = None,
        building_id: int | None = None,
        building_address: str | None = None,
        room_id: int | None = None,
        room_number: str | None = None,
        item_date: date | None = None,
        time_slot: str | None = None,
        schedule_id: int | None = None,
        booking_id: int | None = None,
        course_id: int | None = None,
    ) -> ScheduleItem | None:
        data: dict[str, Any] = {
            "title": title,
            "instructor_id": instructor_id,
            "instructor_name": instructor_name,
            "building_id": building_id,
            "building_address": building_address,
            "room_id": room_id,
            "room_number": room_number,
            "time_slot": time_slot,
            "schedule_id": schedule_id,
            "booking_id": booking_id,
            "course_id": course_id,
        }

        if item_type is not None:
            data["type"] = item_type
        if item_date is not None:
            data["date"] = item_date

        return await self.update_by_id(schedule_item_id, **data)

    async def set_booking_id(
        self,
        schedule_item_id: int,
        booking_id: int | None,
    ) -> ScheduleItem | None:
        item = await self.get_by_id(schedule_item_id)

        if item is None:
            return None

        item.booking_id = booking_id
        await self.session.commit()
        await self.session.refresh(item)

        return item

    async def delete_schedule_item(self, schedule_item_id: int) -> bool:
        return await self.delete_by_id(schedule_item_id)


class ScheduleServiceDAO:
    """
    Facade DAO for the schedule service.

    Use this from service handlers when one object should expose every schedule
    DAO through the same AsyncSession.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

        self.academic_years = AcademicYearDAO(session)
        self.modules = ModuleDAO(session)
        self.holidays = HolidayDAO(session)
        self.programmes = ProgrammeDAO(session)
        self.courses = CourseDAO(session)
        self.course_instructors = CourseInstructorDAO(session)
        self.groups = GroupDAO(session)
        self.group_students = GroupStudentDAO(session)
        self.schedules = ScheduleDAO(session)
        self.schedule_items = ScheduleItemDAO(session)

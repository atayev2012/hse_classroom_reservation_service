from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class AcademicYearCreateRequest(BaseModel):
    name: str
    start_date: str
    end_date: str


class AcademicYearUpdateRequest(BaseModel):
    name: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class ModuleCreateRequest(BaseModel):
    name: str
    start_date: str
    end_date: str
    academic_year_id: int


class ModuleUpdateRequest(BaseModel):
    name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    academic_year_id: int | None = None


class HolidayCreateRequest(BaseModel):
    date: str
    name: str | None = None
    description: str | None = None
    academic_year_id: int


class HolidayUpdateRequest(BaseModel):
    date: str | None = None
    name: str | None = None
    description: str | None = None
    academic_year_id: int | None = None


class ProgrammeCreateRequest(BaseModel):
    name: str
    description: str | None = None


class ProgrammeUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class CourseInstructorRequest(BaseModel):
    instructor_id: int
    instructor_name: str


class CourseCreateRequest(BaseModel):
    name: str
    description: str | None = None
    programme_id: int
    instructors: list[CourseInstructorRequest] = Field(default_factory=list)


class CourseUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    programme_id: int | None = None
    instructors: list[CourseInstructorRequest] | None = None


class GroupStudentRequest(BaseModel):
    user_id: int
    user_email: EmailStr


class GroupStudentUpdateRequest(BaseModel):
    user_email: EmailStr | None = None
    group_id: int | None = None


class GroupCreateRequest(BaseModel):
    name: str
    email: EmailStr
    programme_id: int
    students: list[GroupStudentRequest] = Field(default_factory=list)


class GroupUpdateRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    programme_id: int | None = None


class ScheduleCreateRequest(BaseModel):
    name: str
    module_id: int
    group_id: int


class ScheduleUpdateRequest(BaseModel):
    name: str | None = None
    module_id: int | None = None
    group_id: int | None = None
    is_published: bool | None = None


class ScheduleItemCreateRequest(BaseModel):
    title: str
    item_type: str
    course_id: int | None = None
    instructor_id: int
    instructor_name: str
    building_id: int
    building_address: str
    room_id: int
    room_number: str
    date: str
    time_slot: str
    schedule_id: int
    booking_id: int | None = None


class ScheduleItemUpdateRequest(BaseModel):
    title: str | None = None
    item_type: str | None = None
    course_id: int | None = None
    instructor_id: int | None = None
    instructor_name: str | None = None
    building_id: int | None = None
    building_address: str | None = None
    room_id: int | None = None
    room_number: str | None = None
    date: str | None = None
    time_slot: str | None = None
    schedule_id: int | None = None
    booking_id: int | None = None

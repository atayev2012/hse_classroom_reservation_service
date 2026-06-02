from __future__ import annotations

from database import Base

from sqlalchemy import BigInteger, String, ForeignKey, Date, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date


# Academic year model
class AcademicYear(Base):
    __tablename__ = "academic_years"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    modules: Mapped[list[Module]] = relationship(
        back_populates="academic_year",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    holidays: Mapped[list[Holiday]] = relationship(
        back_populates="academic_year",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


# Education modul model
class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    academic_year_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    academic_year: Mapped[AcademicYear] = relationship(back_populates="modules")
    schedules: Mapped[list[Schedule]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


# Holday model
class Holiday(Base):
    __tablename__ = "holidays"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    academic_year_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    academic_year: Mapped[AcademicYear] = relationship(back_populates="holidays")


# Education programme model
class Programme(Base):
    __tablename__ = "programmes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    groups: Mapped[list[Group]] = relationship(
        back_populates="programme",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    courses: Mapped[list[Course]] = relationship(
        back_populates="programme",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


# Course model
class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    programme_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    programme: Mapped[Programme] = relationship(back_populates="courses")
    instructors: Mapped[list[CourseInstructor]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    schedule_items: Mapped[list[ScheduleItem]] = relationship(back_populates="course")


# Course instructor model
class CourseInstructor(Base):
    __tablename__ = "course_instructors"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    instructor_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    instructor_name: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    course: Mapped[Course] = relationship(back_populates="instructors")

# Education programme group model
class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    programme_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("programmes.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    programme: Mapped[Programme] = relationship(back_populates="groups")
    students: Mapped[list[GroupStudent]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    schedules: Mapped[list[Schedule]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


# Student belonging to a group model
class GroupStudent(Base):
    __tablename__ = "group_students"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    user_email: Mapped[str] = mapped_column(String, nullable=False)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    group: Mapped[Group] = relationship(back_populates="students")


# Schedule model
class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False) 
    module_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("modules.id", ondelete="CASCADE"), nullable=False)
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    module: Mapped[Module] = relationship(back_populates="schedules")
    group: Mapped[Group] = relationship(back_populates="schedules")
    schedule_items: Mapped[list[ScheduleItem]] = relationship(
        back_populates="schedule",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


# Schedule item model
class ScheduleItem(Base):
    __tablename__ = "schedule_items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False) # Lection, Seminar, Exam
    instructor_id: Mapped[int] = mapped_column(BigInteger, nullable=False) # user_id
    instructor_name: Mapped[str] = mapped_column(String, nullable=False) # user full name
    building_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    building_address: Mapped[str] = mapped_column(String, nullable=False)
    room_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    room_number: Mapped[str] = mapped_column(String, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time_slot: Mapped[str] = mapped_column(String, nullable=False)
    schedule_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False)
    booking_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    course_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("courses.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    schedule: Mapped[Schedule] = relationship(back_populates="schedule_items")
    course: Mapped[Course | None] = relationship(back_populates="schedule_items")

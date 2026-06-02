from __future__ import annotations
from database import Base
from sqlalchemy import BigInteger, String, ForeignKey, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum


# enum for user roles
class UserType(str, enum.Enum):
    STUDENT = "student"
    EMPLOYEE = "employee"
    MANAGER = "manager"
    ADMIN = "admin"


# User model
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    type: Mapped[UserType] = mapped_column(Enum(UserType, name="user_type"), nullable=False)

    first_name: Mapped[str] = mapped_column(String(50), nullable=True)
    last_name: Mapped[str] = mapped_column(String(50), nullable=True)
    middle_name: Mapped[str] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # relationships
    verification: Mapped[UserVerification | None] = relationship(
        back_populates="user", 
        uselist=False, 
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    student_profile: Mapped[StudentProfile | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )
    employee_profile: Mapped[EmployeeProfile | None] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True
    )
 

# Verification code model
class UserVerification(Base):
    __tablename__ = "user_verifications"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    verification_code: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # relationships
    user: Mapped[User] = relationship(back_populates="verification")


# Student Profile Model
class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    group_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    study_program: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # relationships
    user: Mapped[User] = relationship(back_populates="student_profile")


# Employee Profile Model
class EmployeeProfile(Base):
    __tablename__ = "employee_profiles"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    department_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # relationships
    user: Mapped[User] = relationship(back_populates="employee_profile")



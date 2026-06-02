from __future__ import annotations

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    device_info: str | None = None


class VerifyCodeRequest(BaseModel):
    user_id: int
    verification_code: str
    device_info: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class StudentProfileRequest(BaseModel):
    group_name: str | None = None
    study_program: str | None = None


class EmployeeProfileRequest(BaseModel):
    department_name: str | None = None
    position: str | None = None


class UserCreateRequest(BaseModel):
    email: EmailStr
    type: str = "student"
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    is_active: bool = True
    student_profile: StudentProfileRequest | None = None
    employee_profile: EmployeeProfileRequest | None = None


class UserUpdateRequest(BaseModel):
    email: EmailStr | None = None
    type: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    middle_name: str | None = None
    is_active: bool | None = None
    is_deleted: bool | None = None
    student_profile: StudentProfileRequest | None = None
    employee_profile: EmployeeProfileRequest | None = None

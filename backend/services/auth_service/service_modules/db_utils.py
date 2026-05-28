from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from service_modules.models import (
    EmployeeProfile,
    StudentProfile,
    User,
    UserType,
    UserVerification,
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

    async def count(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model).filter_by(**filters)
        result = await self.session.execute(stmt)
        return result.scalar_one()


class UserDAO(BaseDAO[User]):
    model = User

    @staticmethod
    def _relationships():
        return (
            selectinload(User.verification),
            selectinload(User.student_profile),
            selectinload(User.employee_profile),
        )

    async def create_user(
        self,
        email: str,
        user_type: UserType,
        first_name: str | None = None,
        last_name: str | None = None,
        middle_name: str | None = None,
        is_active: bool = True,
    ) -> User:
        user = User(
            email=email,
            type=user_type,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            is_active=is_active,
            is_deleted=False,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_by_id(
        self,
        user_id: int,
        load_relationships: bool = False,
    ) -> User | None:
        stmt = select(User).where(User.id == user_id)

        if load_relationships:
            stmt = stmt.options(*self._relationships())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(
        self,
        email: str,
        load_relationships: bool = False,
    ) -> User | None:
        stmt = select(User).where(User.email == email)

        if load_relationships:
            stmt = stmt.options(*self._relationships())

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_users(
        self,
        user_type: UserType | None = None,
        is_active: bool | None = None,
        is_deleted: bool | None = False,
        limit: int = 100,
        offset: int = 0,
        load_relationships: bool = False,
    ) -> Sequence[User]:
        stmt = select(User)

        if load_relationships:
            stmt = stmt.options(*self._relationships())
        if user_type is not None:
            stmt = stmt.where(User.type == user_type)
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        if is_deleted is not None:
            stmt = stmt.where(User.is_deleted == is_deleted)

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_user(
        self,
        user_id: int,
        email: str | None = None,
        user_type: UserType | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        middle_name: str | None = None,
        is_active: bool | None = None,
        is_deleted: bool | None = None,
    ) -> User | None:
        user = await self.get_user_by_id(user_id)

        if user is None:
            return None

        if email is not None:
            user.email = email
        if user_type is not None:
            user.type = user_type
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if middle_name is not None:
            user.middle_name = middle_name
        if is_active is not None:
            user.is_active = is_active
        if is_deleted is not None:
            user.is_deleted = is_deleted

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def soft_delete_user(self, user_id: int) -> bool:
        user = await self.get_user_by_id(user_id)

        if user is None:
            return False

        user.is_deleted = True
        user.is_active = False
        await self.session.commit()
        return True


class UserVerificationDAO(BaseDAO[UserVerification]):
    model = UserVerification

    async def create_or_update_code(
        self,
        user_id: int,
        verification_code: str,
    ) -> UserVerification:
        verification = await self.get_by_user_id(user_id)

        if verification is None:
            verification = UserVerification(
                user_id=user_id,
                verification_code=verification_code,
            )
            self.session.add(verification)
        else:
            verification.verification_code = verification_code

        await self.session.commit()
        await self.session.refresh(verification)
        return verification

    async def get_by_user_id(
        self,
        user_id: int,
        load_user: bool = False,
    ) -> UserVerification | None:
        stmt = select(UserVerification).where(UserVerification.user_id == user_id)

        if load_user:
            stmt = stmt.options(selectinload(UserVerification.user))

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def verify_code(self, user_id: int, code: str) -> bool:
        stmt = select(UserVerification).where(
            UserVerification.user_id == user_id,
            UserVerification.verification_code == code,
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def clear_code(self, user_id: int) -> bool:
        verification = await self.get_by_user_id(user_id)

        if verification is None:
            return False

        verification.verification_code = None
        await self.session.commit()
        return True

    async def delete_code(self, user_id: int) -> bool:
        stmt = delete(UserVerification).where(UserVerification.user_id == user_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0


class StudentProfileDAO(BaseDAO[StudentProfile]):
    model = StudentProfile

    async def create_or_update(
        self,
        user_id: int,
        group_name: str | None = None,
        study_program: str | None = None,
    ) -> StudentProfile:
        profile = await self.get_by_user_id(user_id)

        if profile is None:
            profile = StudentProfile(
                user_id=user_id,
                group_name=group_name,
                study_program=study_program,
            )
            self.session.add(profile)
        else:
            if group_name is not None:
                profile.group_name = group_name
            if study_program is not None:
                profile.study_program = study_program

        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def get_by_user_id(self, user_id: int) -> StudentProfile | None:
        stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class EmployeeProfileDAO(BaseDAO[EmployeeProfile]):
    model = EmployeeProfile

    async def create_or_update(
        self,
        user_id: int,
        department_name: str | None = None,
        position: str | None = None,
    ) -> EmployeeProfile:
        profile = await self.get_by_user_id(user_id)

        if profile is None:
            profile = EmployeeProfile(
                user_id=user_id,
                department_name=department_name,
                position=position,
            )
            self.session.add(profile)
        else:
            if department_name is not None:
                profile.department_name = department_name
            if position is not None:
                profile.position = position

        await self.session.commit()
        await self.session.refresh(profile)
        return profile

    async def get_by_user_id(self, user_id: int) -> EmployeeProfile | None:
        stmt = select(EmployeeProfile).where(EmployeeProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class AuthServiceDAO:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserDAO(session)
        self.verifications = UserVerificationDAO(session)
        self.students = StudentProfileDAO(session)
        self.employees = EmployeeProfileDAO(session)

    async def get_full_user_by_id(self, user_id: int) -> User | None:
        return await self.users.get_user_by_id(
            user_id=user_id,
            load_relationships=True,
        )

    async def get_full_user_by_email(self, email: str) -> User | None:
        return await self.users.get_user_by_email(
            email=email,
            load_relationships=True,
        )

    async def get_or_create_user_for_login(self, email: str) -> User:
        user = await self.users.get_user_by_email(email)

        if user is not None:
            return user

        return await self.users.create_user(
            email=email,
            user_type=UserType.STUDENT,
        )

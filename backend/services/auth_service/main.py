from __future__ import annotations

import asyncio
import logging
import logging.config
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import auth_service_pb2
import auth_service_pb2_grpc
import grpc
import notification_service_pb2
import notification_service_pb2_grpc

from database import async_session_maker
from service_modules.config import LOGGING_CONFIG, jwt_config, service_config
from service_modules.db_utils import AuthServiceDAO
from service_modules.models import EmployeeProfile, StudentProfile, User, UserType
from service_modules.security import email_validate, generate_verification_code

Path("logs").mkdir(exist_ok=True)
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("auth_microservice")


class NotificationClient:
    def __init__(self, target: str):
        self.channel = grpc.aio.insecure_channel(target)
        self.stub = notification_service_pb2_grpc.NotificationServiceStub(self.channel)

    async def send_verification_code(
        self,
        email: str,
        code: str,
        valid_till: datetime,
        ip_address: str = "",
        request_datetime: str = "",
        device_info: str = "",
    ) -> None:
        await self.stub.SendVerificationCode(
            notification_service_pb2.VerificationCodeRequest(
                email=email,
                code=code,
                verification_url=service_config.VERIFICATION_URL,
                code_valid_till=valid_till.isoformat(),
                ip_address=ip_address,
                request_datetime=(
                    request_datetime or datetime.now(timezone.utc).isoformat()
                ),
                device_info=device_info,
            )
        )

    async def send_login_successful(
        self,
        email: str,
        ip_address: str = "",
        request_datetime: str = "",
        device_info: str = "",
    ) -> None:
        await self.stub.SendLoginSuccessful(
            notification_service_pb2.LoginSuccessfulRequest(
                email=email,
                ip_address=ip_address,
                request_datetime=(
                    request_datetime or datetime.now(timezone.utc).isoformat()
                ),
                device_info=device_info,
            )
        )

    async def close(self) -> None:
        await self.channel.close()


class AuthService(auth_service_pb2_grpc.AuthServiceServicer):
    def __init__(
        self,
        session_factory=async_session_maker,
        notification_client: NotificationClient | None = None,
    ):
        self.session_factory = session_factory
        self.notification_client = notification_client
        self._background_tasks: set[asyncio.Task] = set()

    async def HealthCheck(self, request, context):
        try:
            return auth_service_pb2.HealthCheckResponse(
                success=True,
                status="SERVING",
            )
        except asyncio.TimeoutError:
            logger.exception("Auth service health check timed out")
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Health check timed out")
            return auth_service_pb2.HealthCheckResponse(
                success=False,
                status="TIMEOUT",
            )
        except Exception as exc:
            logger.exception("Auth service health check failed")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(str(exc))
            return auth_service_pb2.HealthCheckResponse(
                success=False,
                status="UNAVAILABLE",
            )

    async def Login(self, request, context):
        email = (request.email or "").lower().strip()

        if not email or not await email_validate(email):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid HSE email")

        async with self.session_factory() as session:
            dao = AuthServiceDAO(session)
            user = await dao.get_or_create_user_for_login(email)
            code = await generate_verification_code()
            verification = await dao.verifications.create_or_update_code(
                user_id=user.id,
                verification_code=code,
            )

        valid_till = datetime.now(timezone.utc) + timedelta(
            minutes=service_config.VERIFICATION_CODE_VALID_MINUTES
        )
        self._schedule_background_notification(
            "verification code",
            self.notification_client.send_verification_code(
                email=email,
                code=code,
                valid_till=valid_till,
                ip_address=_optional_value(request, "ip_address", ""),
                request_datetime=_optional_value(request, "request_datetime", ""),
                device_info=_optional_value(request, "device_info", ""),
            ) if self.notification_client else None,
        )

        return auth_service_pb2.UserVerification(
            user_id=verification.user_id,
            verification_code=verification.verification_code,
        )

    async def VerifyCode(self, request, context):
        async with self.session_factory() as session:
            dao = AuthServiceDAO(session)
            is_valid = await dao.verifications.verify_code(
                request.user_id,
                request.verification_code,
            )

            if not is_valid:
                return auth_service_pb2.VerifyCodeResponse(
                    success=False,
                    status="Invalid verification code",
                )

            user = await dao.get_full_user_by_id(request.user_id)

            if user is None or not user.is_active or user.is_deleted:
                return auth_service_pb2.VerifyCodeResponse(
                    success=False,
                    status="User is not active",
                )

            await dao.verifications.clear_code(user.id)

        payload = {"user_id": user.id, "email": user.email, "type": user.type.value}
        access_token = jwt_config.generate_token(payload, token_type="access")
        refresh_token = jwt_config.generate_token(payload, token_type="refresh")

        self._schedule_background_notification(
            "login successful",
            self.notification_client.send_login_successful(
                user.email,
                ip_address=_optional_value(request, "ip_address", ""),
                request_datetime=_optional_value(request, "request_datetime", ""),
                device_info=_optional_value(request, "device_info", ""),
            )
            if self.notification_client
            else None,
        )

        return auth_service_pb2.VerifyCodeResponse(
            success=True,
            status="OK",
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def RefreshToken(self, request, context):
        async with self.session_factory() as session:
            dao = AuthServiceDAO(session)
            user = await dao.get_full_user_by_id(request.user_id)

        if user is None or not user.is_active or user.is_deleted:
            return auth_service_pb2.RefreshTokenResponse(
                success=False,
                status="User is not active",
            )

        access_token = jwt_config.generate_token(
            {"user_id": user.id, "email": user.email, "type": user.type.value},
            token_type="access",
        )

        return auth_service_pb2.RefreshTokenResponse(
            success=True,
            status="OK",
            access_token=access_token,
        )

    async def Me(self, request, context):
        return await self.GetSingleUser(request, context)

    async def GetAllStudents(self, request, context):
        async with self.session_factory() as session:
            dao = AuthServiceDAO(session)
            users = await dao.users.get_users(
                user_type=UserType.STUDENT,
                load_relationships=True,
            )

        filtered = []
        for user in users:
            profile = user.student_profile
            if profile is None:
                continue
            if _has_field(request, "group_name") and profile.group_name != request.group_name:
                continue
            if (
                _has_field(request, "study_program")
                and profile.study_program != request.study_program
            ):
                continue
            filtered.append(_user_to_proto(user))

        return auth_service_pb2.AllStudentsResponse(
            success=True,
            status="OK",
            users=filtered,
        )

    async def GetAllUsers(self, request, context):
        requested_types = {
            _parse_user_type(type_value)
            for type_value in request.types
            if type_value
        }
        if _has_field(request, "type") and request.type:
            requested_types.add(_parse_user_type(request.type))
        user_type = next(iter(requested_types)) if len(requested_types) == 1 else None
        limit = max(_optional_value(request, "limit", 100), 1)
        offset = max(_optional_value(request, "offset", 0), 0)

        async with self.session_factory() as session:
            dao = AuthServiceDAO(session)
            users = await dao.users.get_users(
                user_type=user_type,
                is_deleted=(
                    request.is_deleted
                    if _has_field(request, "is_deleted")
                    else False
                ),
                limit=10000,
                offset=0,
                load_relationships=True,
            )

        filtered_users = [
            user for user in users if _user_matches_all_users_request(user, request, requested_types)
        ]
        paged_users = filtered_users[offset:offset + limit]

        return auth_service_pb2.AllUsersResponse(
            success=True,
            status="OK",
            users=[_user_to_proto(user) for user in paged_users],
            total_count=len(filtered_users),
        )

    async def GetSingleUser(self, request, context):
        async with self.session_factory() as session:
            dao = AuthServiceDAO(session)

            if _has_field(request, "id"):
                user = await dao.get_full_user_by_id(request.id)
            elif _has_field(request, "email"):
                user = await dao.get_full_user_by_email(request.email.lower().strip())
            else:
                user = None

        if user is None:
            return auth_service_pb2.UserResponse(
                success=False,
                status="User not found",
            )

        return auth_service_pb2.UserResponse(
            success=True,
            status="OK",
            user=_user_to_proto(user),
        )

    async def AddUser(self, request, context):
        email = (request.email or "").lower().strip()
        user_type = _parse_user_type(request.type or "student")

        async with self.session_factory() as session:
            dao = AuthServiceDAO(session)
            existing = await dao.users.get_user_by_email(email)

            if existing is not None:
                return auth_service_pb2.UserResponse(
                    success=False,
                    status="User already exists",
                    user=_user_to_proto(existing),
                )

            user = await dao.users.create_user(
                email=email,
                user_type=user_type,
                first_name=_optional_value(request, "first_name"),
                last_name=_optional_value(request, "last_name"),
                middle_name=_optional_value(request, "middle_name"),
                is_active=_optional_value(request, "is_active", True),
            )

            if user_type == UserType.STUDENT and request.HasField("student_profile"):
                await dao.students.create_or_update(
                    user_id=user.id,
                    group_name=_optional_value(request.student_profile, "group_name"),
                    study_program=_optional_value(
                        request.student_profile,
                        "study_program",
                    ),
                )
            elif request.HasField("employee_profile"):
                await dao.employees.create_or_update(
                    user_id=user.id,
                    department_name=_optional_value(
                        request.employee_profile,
                        "department_name",
                    ),
                    position=_profile_position(request.employee_profile),
                )

            user = await dao.get_full_user_by_id(user.id)

        return auth_service_pb2.UserResponse(
            success=True,
            status="Created",
            user=_user_to_proto(user),
        )

    async def UpdateUser(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = AuthServiceDAO(session)
            user = await dao.users.update_user(
                user_id=request.id,
                email=_optional_value(request, "email"),
                user_type=_parse_user_type(request.type) if _has_field(request, "type") else None,
                first_name=_optional_value(request, "first_name"),
                last_name=_optional_value(request, "last_name"),
                middle_name=_optional_value(request, "middle_name"),
                is_active=_optional_value(request, "is_active"),
                is_deleted=_optional_value(request, "is_deleted"),
            )

            if user is None:
                return auth_service_pb2.UserResponse(
                    success=False,
                    status="User not found",
                )

            if request.HasField("student_profile"):
                await dao.students.create_or_update(
                    user_id=user.id,
                    group_name=_optional_value(request.student_profile, "group_name"),
                    study_program=_optional_value(
                        request.student_profile,
                        "study_program",
                    ),
                )

            if request.HasField("employee_profile"):
                await dao.employees.create_or_update(
                    user_id=user.id,
                    department_name=_optional_value(
                        request.employee_profile,
                        "department_name",
                    ),
                    position=_profile_position(request.employee_profile),
                )

            user_id = user.id
            session.expire_all()
            user = await dao.get_full_user_by_id(user_id)

        return auth_service_pb2.UserResponse(
            success=True,
            status="Updated",
            user=_user_to_proto(user),
        )

    async def DeleteUser(self, request, context):
        if not _has_field(request, "id"):
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, "id is required")

        async with self.session_factory() as session:
            dao = AuthServiceDAO(session)
            success = await dao.users.soft_delete_user(request.id)
            user = await dao.get_full_user_by_id(request.id)

        response = auth_service_pb2.UserResponse(
            success=success,
            status="Deleted" if success else "User not found",
        )
        if user is not None:
            response.user.CopyFrom(_user_to_proto(user))
        return response

    def _schedule_background_notification(
        self,
        label: str,
        coroutine,
    ) -> None:
        if coroutine is None:
            return

        task = asyncio.create_task(coroutine)
        self._background_tasks.add(task)

        def _done(done_task: asyncio.Task) -> None:
            self._background_tasks.discard(done_task)
            try:
                done_task.result()
            except Exception:
                logger.exception("Background notification failed: %s", label)

        task.add_done_callback(_done)


def _has_field(message, field_name: str) -> bool:
    try:
        return message.HasField(field_name)
    except ValueError:
        return bool(getattr(message, field_name))


def _optional_value(message, field_name: str, default=None):
    return getattr(message, field_name) if _has_field(message, field_name) else default


def _parse_user_type(value: str) -> UserType:
    normalized = (value or "student").lower()

    for user_type in UserType:
        if user_type.value == normalized or user_type.name.lower() == normalized:
            return user_type

    return UserType.STUDENT


def _profile_position(profile) -> str | None:
    if hasattr(profile, "position"):
        return _optional_value(profile, "position")
    return _optional_value(profile, "poisition")


def _user_matches_all_users_request(
    user: User,
    request,
    requested_types: set[UserType],
) -> bool:
    if requested_types and user.type not in requested_types:
        return False
    if _has_field(request, "id") and user.id != request.id:
        return False
    if _has_field(request, "is_active") and user.is_active != request.is_active:
        return False
    if _has_field(request, "full_name") and not _contains(
        " ".join(
            value for value in (user.last_name, user.first_name, user.middle_name) if value
        ),
        request.full_name,
    ):
        return False

    string_checks = (
        ("email", user.email),
        ("first_name", user.first_name),
        ("last_name", user.last_name),
        ("middle_name", user.middle_name),
    )
    for field_name, value in string_checks:
        if _has_field(request, field_name) and not _contains(value, getattr(request, field_name)):
            return False

    student_profile = user.student_profile
    if _has_field(request, "group_name") and not _contains(
        student_profile.group_name if student_profile else None,
        request.group_name,
    ):
        return False
    if _has_field(request, "study_program") and not _contains(
        student_profile.study_program if student_profile else None,
        request.study_program,
    ):
        return False

    employee_profile = user.employee_profile
    if _has_field(request, "department_name") and not _contains(
        employee_profile.department_name if employee_profile else None,
        request.department_name,
    ):
        return False
    if _has_field(request, "position") and not _contains(
        employee_profile.position if employee_profile else None,
        request.position,
    ):
        return False

    return True


def _contains(value: str | None, query: str | None) -> bool:
    if query is None or query == "":
        return True
    return query.casefold() in (value or "").casefold()


def _user_to_proto(user: User | None):
    if user is None:
        return None

    user_proto = auth_service_pb2.User(
        id=user.id,
        email=user.email,
        type=user.type.value,
        is_active=user.is_active,
        is_deleted=user.is_deleted,
    )

    _set_optional_string(user_proto, "first_name", user.first_name)
    _set_optional_string(user_proto, "last_name", user.last_name)
    _set_optional_string(user_proto, "middle_name", user.middle_name)

    if user.verification is not None:
        user_proto.verification.CopyFrom(
            auth_service_pb2.UserVerification(
                user_id=user.verification.user_id,
                verification_code=user.verification.verification_code,
            )
        )

    if isinstance(user.student_profile, StudentProfile):
        user_proto.student_profile.CopyFrom(
            auth_service_pb2.StudentProfile(
                user_id=user.student_profile.user_id,
                group_name=user.student_profile.group_name,
                study_program=user.student_profile.study_program,
            )
        )

    if isinstance(user.employee_profile, EmployeeProfile):
        user_proto.employee_profile.CopyFrom(
            auth_service_pb2.EmployeeProfile(
                user_id=user.employee_profile.user_id,
                department_name=user.employee_profile.department_name,
                position=user.employee_profile.position,
            )
        )

    return user_proto


def _set_optional_string(message, field_name: str, value: str | None) -> None:
    if value is not None:
        setattr(message, field_name, value)


async def serve() -> None:
    target = (
        f"{service_config.NOTIFICATION_SERVICE_HOST}:"
        f"{service_config.NOTIFICATION_SERVICE_PORT}"
    )
    notification_client = NotificationClient(target)

    server = grpc.aio.server()
    auth_service_pb2_grpc.add_AuthServiceServicer_to_server(
        AuthService(notification_client=notification_client),
        server,
    )

    listen_addr = f"{service_config.HOST}:{service_config.PORT}"
    server.add_insecure_port(listen_addr)
    await server.start()
    logger.info("Auth service started at %s", listen_addr)

    try:
        await server.wait_for_termination()
    finally:
        await notification_client.close()


if __name__ == "__main__":
    asyncio.run(serve())

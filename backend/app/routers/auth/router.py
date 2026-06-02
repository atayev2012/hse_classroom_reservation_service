from __future__ import annotations

import auth_service_pb2
from fastapi import APIRouter, Body, Depends, Query, Request, Response

from dependencies import clear_token_cookies, get_current_user, issue_access_token_from_refresh, require_roles, set_token_cookies
from grpc_utils import proto_to_dict
from health import check_grpc_health

from .schemas import LoginRequest, RefreshRequest, UserCreateRequest, UserUpdateRequest, VerifyCodeRequest
from .utils import device_info, request_datetime, request_ip, user_create_to_proto, user_update_to_proto

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/health")
async def health(request: Request):
    return await check_grpc_health(
        request.app.state.auth_stub,
        auth_service_pb2.HealthCheckRequest(),
        "auth service",
    )


@router.post("/login")
async def login(payload: LoginRequest, request: Request):
    response = await request.app.state.auth_stub.Login(
        auth_service_pb2.User(
            email=payload.email,
            ip_address=request_ip(request),
            request_datetime=request_datetime(),
            device_info=device_info(request, payload.device_info),
        )
    )
    return proto_to_dict(response)


@router.post("/verify")
async def verify_code(payload: VerifyCodeRequest, request: Request, response: Response):
    grpc_response = await request.app.state.auth_stub.VerifyCode(
        auth_service_pb2.UserVerification(
            user_id=payload.user_id,
            verification_code=payload.verification_code,
            ip_address=request_ip(request),
            request_datetime=request_datetime(),
            device_info=device_info(request, payload.device_info),
        )
    )
    data = proto_to_dict(grpc_response)
    if grpc_response.success:
        set_token_cookies(
            response=response,
            access_token=grpc_response.access_token,
            refresh_token=grpc_response.refresh_token,
        )
    return data


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    payload: RefreshRequest | None = Body(default=None),
):
    refresh_token = (
        payload.refresh_token
        if payload and payload.refresh_token
        else request.cookies.get("hse_refresh_token") or request.headers.get("x-refresh-token")
    )
    if not refresh_token:
        return {"success": False, "status": "Missing refresh token"}
    token_payload, access_token = await issue_access_token_from_refresh(request, refresh_token)
    set_token_cookies(response, access_token)
    return {
        "success": True,
        "status": "OK",
        "access_token": access_token,
        "user_id": token_payload.get("user_id"),
    }


@router.post("/logout")
async def logout(response: Response):
    clear_token_cookies(response)
    return {"success": True, "status": "Logged out"}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@router.get("/students")
async def get_students(
    request: Request,
    study_program: str | None = None,
    group_name: str | None = None,
    _: dict = Depends(require_roles("employee", "manager", "admin")),
):
    grpc_request = auth_service_pb2.AllStudentsRequest()
    if study_program is not None:
        grpc_request.study_program = study_program
    if group_name is not None:
        grpc_request.group_name = group_name
    response = await request.app.state.auth_stub.GetAllStudents(grpc_request)
    return proto_to_dict(response)


@router.get("/users")
async def get_users(
    request: Request,
    type: str | None = None,
    id: int | None = None,
    types: list[str] | None = Query(default=None),
    is_deleted: bool | None = False,
    is_active: bool | None = None,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
    middle_name: str | None = None,
    full_name: str | None = None,
    group_name: str | None = None,
    study_program: str | None = None,
    department_name: str | None = None,
    position: str | None = None,
    limit: int | None = 100,
    offset: int | None = 0,
    _: dict = Depends(require_roles("manager", "admin")),
):
    grpc_request = auth_service_pb2.AllUsersRequest()
    if type is not None:
        grpc_request.type = type
    if id is not None:
        grpc_request.id = id
    if types:
        grpc_request.types.extend(types)
    if is_deleted is not None:
        grpc_request.is_deleted = is_deleted
    if is_active is not None:
        grpc_request.is_active = is_active
    for field_name, value in (
        ("email", email),
        ("first_name", first_name),
        ("last_name", last_name),
        ("middle_name", middle_name),
        ("full_name", full_name),
        ("group_name", group_name),
        ("study_program", study_program),
        ("department_name", department_name),
        ("position", position),
    ):
        if value is not None:
            setattr(grpc_request, field_name, value)
    if limit is not None:
        grpc_request.limit = limit
    if offset is not None:
        grpc_request.offset = offset
    response = await request.app.state.auth_stub.GetAllUsers(grpc_request)
    return proto_to_dict(response)


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    request: Request,
    _: dict = Depends(require_roles("employee", "manager", "admin")),
):
    response = await request.app.state.auth_stub.GetSingleUser(
        auth_service_pb2.User(id=user_id)
    )
    return proto_to_dict(response)


@router.post("/users")
async def create_user(
    payload: UserCreateRequest,
    request: Request,
    _: dict = Depends(require_roles("manager", "admin")),
):
    response = await request.app.state.auth_stub.AddUser(user_create_to_proto(payload))
    return proto_to_dict(response)


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    request: Request,
    _: dict = Depends(require_roles("manager", "admin")),
):
    response = await request.app.state.auth_stub.UpdateUser(
        user_update_to_proto(user_id, payload)
    )
    return proto_to_dict(response)


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request,
    _: dict = Depends(require_roles("manager", "admin")),
):
    response = await request.app.state.auth_stub.DeleteUser(
        auth_service_pb2.User(id=user_id)
    )
    return proto_to_dict(response)

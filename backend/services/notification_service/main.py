from __future__ import annotations

import asyncio
import logging
import logging.config
from pathlib import Path
from typing import Any

import grpc
import notification_service_pb2
import notification_service_pb2_grpc
from google.protobuf.json_format import MessageToDict

from database import async_session_maker
from service_modules.config import LOGGING_CONFIG, service_config
from service_modules.db_utils import NotificationServiceDAO
from service_modules.email import EmailSender, EmailSendResult

Path("logs").mkdir(exist_ok=True)
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)


class NotificationService(
    notification_service_pb2_grpc.NotificationServiceServicer
):
    def __init__(
        self,
        email_sender: EmailSender | None = None,
        session_factory=async_session_maker,
    ):
        self.email_sender = email_sender or EmailSender()
        self.session_factory = session_factory

    async def HealthCheck(self, request, context):
        try:
            return notification_service_pb2.HealthCheckResponse(
                success=True,
                status="SERVING",
            )
        except asyncio.TimeoutError:
            logger.exception("Notification service health check timed out")
            context.set_code(grpc.StatusCode.DEADLINE_EXCEEDED)
            context.set_details("Health check timed out")
            return notification_service_pb2.HealthCheckResponse(
                success=False,
                status="TIMEOUT",
            )
        except Exception as exc:
            logger.exception("Notification service health check failed")
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            context.set_details(str(exc))
            return notification_service_pb2.HealthCheckResponse(
                success=False,
                status="UNAVAILABLE",
            )

    async def SendVerificationCode(self, request, context):
        subject = "Код подтверждения входа"
        payload = _message_to_dict(request)
        result = await self._send_and_record(
            recipient_email=request.email,
            notification_type="verification_code",
            subject=subject,
            template_name="verification_code.html",
            template_context={
                "email": request.email,
                "code": request.code,
                "verification_url": request.verification_url,
                "code_valid_till": request.code_valid_till,
                "ip_address": request.ip_address,
                "request_datetime": request.request_datetime,
                "device_info": request.device_info,
            },
            payload=payload,
        )

        return _response(result)

    async def SendLoginSuccessful(self, request, context):
        subject = "Успешный вход в систему"
        payload = _message_to_dict(request)
        result = await self._send_and_record(
            recipient_email=request.email,
            notification_type="login_successful",
            subject=subject,
            template_name="login_successful.html",
            template_context={
                "email": request.email,
                "ip_address": request.ip_address,
                "request_datetime": request.request_datetime,
                "device_info": request.device_info,
            },
            payload=payload,
        )

        return _response(result)

    async def SendReservationNotification(self, request, context):
        subject = f"Бронирование аудитории: {request.status}"
        payload = _message_to_dict(request)
        result = await self._send_and_record(
            recipient_email=request.email,
            notification_type="reservation",
            subject=subject,
            template_name="reservation_notification.html",
            template_context={
                "building_name": request.building_name,
                "room_number": request.room_number,
                "event_date": request.event_date,
                "time_slot": request.time_slot,
                "status": request.status,
                "email": request.email,
            },
            payload=payload,
        )

        return _response(result)

    async def SendSchedulePublished(self, request, context):
        group = _group_context(request.group)
        subject = f"Опубликовано расписание: {request.schedule_name}"
        payload = _message_to_dict(request)
        result = await self._send_and_record(
            recipient_email=group["group_email"],
            notification_type="schedule_published",
            subject=subject,
            template_name="schedule_published.html",
            template_context={
                "manager_email": request.manager_email,
                "schedule_name": request.schedule_name,
                "module_name": request.module_name,
                **group,
            },
            payload=payload,
        )

        return _response(result)

    async def SendScheduleAddedItem(self, request, context):
        item = _item_context(request.schedule_item)
        subject = f"Добавлено занятие: {item['title']}"
        payload = _message_to_dict(request)
        result = await self._send_and_record(
            recipient_email=item["group_email"],
            notification_type="schedule_item_added",
            subject=subject,
            template_name="schedule_item.html",
            template_context={
                "action_title": "Занятие добавлено",
                "manager_email": request.manager_email,
                **item,
            },
            payload=payload,
        )

        return _response(result)

    async def SendScheduleDeletedItem(self, request, context):
        item = _item_context(request.schedule_item)
        subject = f"Удалено занятие: {item['title']}"
        payload = _message_to_dict(request)
        result = await self._send_and_record(
            recipient_email=item["group_email"],
            notification_type="schedule_item_deleted",
            subject=subject,
            template_name="schedule_item.html",
            template_context={
                "action_title": "Занятие удалено",
                "manager_email": request.manager_email,
                **item,
            },
            payload=payload,
        )

        return _response(result)

    async def SendScheduleEditedItem(self, request, context):
        old_item = _item_context(request.unedited_item)
        item = _item_context(request.edited_item)
        subject = f"Изменено занятие: {item['title']}"
        payload = _message_to_dict(request)
        result = await self._send_and_record(
            recipient_email=item["group_email"] or old_item["group_email"],
            notification_type="schedule_item_edited",
            subject=subject,
            template_name="schedule_item_edited.html",
            template_context={
                "manager_email": request.manager_email,
                **item,
                "old_title": old_item["title"],
                "old_date": old_item["date"],
                "old_time_slot": old_item["time_slot"],
                "old_room_number": old_item["room_number"],
            },
            payload=payload,
        )

        return _response(result)

    async def _send_and_record(
        self,
        recipient_email: str,
        notification_type: str,
        subject: str,
        template_name: str,
        template_context: dict[str, Any],
        payload: dict | None = None,
    ) -> EmailSendResult:
        recipient_email = recipient_email or "unknown"

        if recipient_email == "unknown":
            result = EmailSendResult(
                success=False,
                details="Recipient email is missing",
                error_message="recipient_email is required",
            )
        else:
            result = await self.email_sender.send_template(
                to_email=recipient_email,
                subject=subject,
                template_name=template_name,
                context=template_context,
            )

        async with self.session_factory() as session:
            dao = NotificationServiceDAO(session)
            await dao.history.record(
                recipient_email=recipient_email,
                notification_type=notification_type,
                subject=subject,
                status="sent" if result.success else "failed",
                details=result.details,
                error_message=result.error_message,
                provider_message_id=result.provider_message_id,
                payload=payload,
            )

        return result


def _message_to_dict(message) -> dict:
    return MessageToDict(
        message,
        preserving_proto_field_name=True,
        always_print_fields_with_no_presence=True,
    )


def _group_context(group) -> dict[str, str]:
    return {
        "programme_name": group.programme_name,
        "group_name": group.group_name,
        "group_email": group.group_email,
    }


def _item_context(item) -> dict[str, Any]:
    group = _group_context(item.group)

    return {
        "id": item.id,
        "title": item.title,
        "item_type": item.item_type,
        "instructor_id": item.instructor_id,
        "instructor_name": item.instructor_name,
        "building_id": item.building_id,
        "building_address": item.building_address,
        "room_id": item.room_id,
        "room_number": item.room_number,
        "date": item.date,
        "time_slot": item.time_slot,
        "schedule_name": item.schedule_name,
        "module_name": item.module_name,
        **group,
    }


def _response(result: EmailSendResult):
    return notification_service_pb2.NotificationResponse(
        success=result.success,
        status="sent" if result.success else "failed",
        details=result.details if result.success else result.error_message or result.details,
    )


async def serve() -> None:
    server = grpc.aio.server()
    notification_service_pb2_grpc.add_NotificationServiceServicer_to_server(
        NotificationService(),
        server,
    )

    listen_addr = f"{service_config.HOST}:{service_config.PORT}"
    server.add_insecure_port(listen_addr)

    await server.start()
    logger.info("Notification service started at %s", listen_addr)

    try:
        await server.wait_for_termination()
    except asyncio.CancelledError:
        await server.stop(grace=5)
        raise


if __name__ == "__main__":
    asyncio.run(serve())

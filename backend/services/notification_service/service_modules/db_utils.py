from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from service_modules.models import NotificationHistory

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


class NotificationHistoryDAO(BaseDAO[NotificationHistory]):
    model = NotificationHistory

    async def record(
        self,
        recipient_email: str,
        notification_type: str,
        subject: str,
        status: str,
        details: str | None = None,
        error_message: str | None = None,
        payload: dict | None = None,
        provider_message_id: str | None = None,
    ) -> NotificationHistory:
        sent_at = datetime.now(timezone.utc) if status == "sent" else None

        return await self.create(
            recipient_email=recipient_email,
            notification_type=notification_type,
            subject=subject,
            status=status,
            details=details,
            error_message=error_message,
            provider_message_id=provider_message_id,
            payload=payload,
            sent_at=sent_at,
        )

    async def get_history(
        self,
        recipient_email: str | None = None,
        notification_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[NotificationHistory]:
        stmt = select(NotificationHistory)

        if recipient_email is not None:
            stmt = stmt.where(NotificationHistory.recipient_email == recipient_email)
        if notification_type is not None:
            stmt = stmt.where(NotificationHistory.notification_type == notification_type)
        if status is not None:
            stmt = stmt.where(NotificationHistory.status == status)

        stmt = (
            stmt.order_by(NotificationHistory.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(stmt)
        return result.scalars().all()


class NotificationServiceDAO:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.history = NotificationHistoryDAO(session)

from __future__ import annotations

import asyncio
import html
import smtplib
from dataclasses import dataclass
from datetime import date, datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from service_modules.config import EmailConfig, email_config

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
DATETIME_FORMAT = "%d.%m.%Y %H:%M:%S"
DATE_FORMAT = "%d.%m.%Y"


def _format_template_value(key: str, value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, datetime):
        return value.strftime(DATETIME_FORMAT)

    if isinstance(value, date):
        return value.strftime(DATE_FORMAT)

    if not isinstance(value, str):
        return str(value)

    text = value.strip()
    if not text:
        return ""

    should_try_date = (
        "timestamp" in key
        or "datetime" in key
        or key.endswith("_at")
        or key.endswith("_date")
        or key.endswith("_till")
        or key in {"date", "created", "updated"}
    )

    if should_try_date:
        normalized = text.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed.strftime(DATETIME_FORMAT)
        except ValueError:
            try:
                parsed_date = date.fromisoformat(text)
                return parsed_date.strftime(DATE_FORMAT)
            except ValueError:
                return text

    return text


@dataclass(frozen=True)
class EmailSendResult:
    success: bool
    details: str
    provider_message_id: str | None = None
    error_message: str | None = None


class TemplateRenderer:
    def __init__(self, template_dir: Path = TEMPLATE_DIR):
        self.template_dir = template_dir

    def render(self, template_name: str, **context: Any) -> str:
        template = (self.template_dir / template_name).read_text(encoding="utf-8")
        values = {
            key: html.escape(_format_template_value(key, value))
            for key, value in context.items()
        }

        for key, value in values.items():
            template = template.replace("{{ " + key + " }}", value)

        return template


class EmailSender:
    def __init__(
        self,
        config: EmailConfig = email_config,
        renderer: TemplateRenderer | None = None,
    ):
        self.config = config
        self.renderer = renderer or TemplateRenderer()

    async def send_template(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: dict[str, Any],
    ) -> EmailSendResult:
        html_body = self.renderer.render(template_name, **context)
        text_body = self._text_fallback(context)

        return await asyncio.to_thread(
            self._send,
            to_email,
            subject,
            text_body,
            html_body,
        )

    def _send(
        self,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str,
    ) -> EmailSendResult:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = f"{self.config.FROM_NAME} <{self.config.FROM_EMAIL}>"
        message["To"] = to_email
        message.set_content(text_body, subtype="plain", charset="utf-8")
        message.add_alternative(html_body, subtype="html", charset="utf-8")

        try:
            smtp_class = smtplib.SMTP_SSL if self.config.USE_SSL else smtplib.SMTP
            with smtp_class(
                self.config.HOST,
                self.config.PORT,
                timeout=self.config.TIMEOUT,
            ) as server:
                if self.config.USE_TLS and not self.config.USE_SSL:
                    server.starttls()

                if self.config.USERNAME and self.config.PASSWORD:
                    server.login(self.config.USERNAME, self.config.PASSWORD)

                refused = server.send_message(message)

            if refused:
                return EmailSendResult(
                    success=False,
                    details="Email was refused by SMTP server",
                    error_message=str(refused),
                )

            return EmailSendResult(success=True, details="Email sent")
        except Exception as exc:
            return EmailSendResult(
                success=False,
                details="Email sending failed",
                error_message=str(exc),
            )

    @staticmethod
    def _text_fallback(context: dict[str, Any]) -> str:
        lines = []

        for key, value in context.items():
            if value is not None:
                lines.append(
                    f"{key.replace('_', ' ').title()}: "
                    f"{_format_template_value(key, value)}"
                )

        return "\n".join(lines) or "Notification"

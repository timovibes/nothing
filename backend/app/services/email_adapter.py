"""
the EmailAdapter interface plus a Gmail SMTP implementation — same swappable-boundary pattern
 as PaymentProcessorAdapter, so a real transactional email provider (SendGrid, SES) can 
 replace this later without touching anything else.
"""

import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


@dataclass
class EmailSendResult:
    success: bool
    error_message: str | None = None


class EmailAdapter(ABC):
    """
    Any real provider (SendGrid, SES, Postmark) implements this exact interface.
    Nothing else in the system depends on which implementation is plugged in —
    swap the adapter, keep every notification-triggering call site unchanged.
    """

    @abstractmethod
    def send(self, to_email: str, subject: str, body: str) -> EmailSendResult:
        ...


class GmailSMTPAdapter(EmailAdapter):
    def send(self, to_email: str, subject: str, body: str) -> EmailSendResult:
        message = MIMEMultipart()
        message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM_EMAIL, to_email, message.as_string())
            return EmailSendResult(success=True)
        except Exception as e:
            return EmailSendResult(success=False, error_message=str(e)[:1000])


def get_email_adapter() -> EmailAdapter:
    # Swap this single line to plug in a real provider later (e.g. SendGridAdapter()).
    return GmailSMTPAdapter()
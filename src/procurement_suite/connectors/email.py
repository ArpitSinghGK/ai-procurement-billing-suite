"""Email connector — IMAP for inbound enquiries, SMTP for outbound.

Vendors and customers who work over email land here. Inbound messages become
``Lead``s; quotations go out over SMTP.
"""
from __future__ import annotations

import uuid

from ..config import get_settings
from ..models import Channel, Lead


class EmailConnector:
    channel = Channel.EMAIL

    def __init__(self) -> None:
        settings = get_settings()
        self._imap_host = settings.email_imap_host
        self._smtp_host = settings.email_smtp_host
        self._username = settings.email_username
        self._password = settings.email_password

    def poll(self) -> list[Lead]:
        """Fetch unread enquiries over IMAP and normalize them to leads."""
        # TODO: connect via imaplib, search UNSEEN, parse each message body.
        return []

    def lead_from_message(self, sender: str, subject: str, body: str) -> Lead:
        return Lead(
            lead_id=str(uuid.uuid4()),
            channel=self.channel,
            customer_contact=sender,
            raw_text=f"{subject}\n\n{body}",
        )

    def send(self, to: str, message: str) -> None:
        # TODO: build a MIME message and send over smtplib (SMTP + STARTTLS).
        ...

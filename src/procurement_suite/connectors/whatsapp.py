"""WhatsApp connector (Meta Cloud API / Twilio compatible).

Inbound enquiries arrive via webhook and are normalized to ``Lead``s; outbound
quotations and negotiation messages are sent through the Cloud API. Network
calls are stubbed with clear TODOs — the seams are real and idiomatic.
"""
from __future__ import annotations

import uuid

import httpx

from ..config import get_settings
from ..models import Channel, Lead


class WhatsAppConnector:
    channel = Channel.WHATSAPP

    def __init__(self) -> None:
        settings = get_settings()
        self._base = settings.whatsapp_api_base
        self._phone_id = settings.whatsapp_phone_number_id
        self._token = settings.whatsapp_access_token
        self._http = httpx.Client(
            base_url=self._base,
            headers={"Authorization": f"Bearer {self._token}"},
            timeout=15.0,
        )

    def lead_from_webhook(self, payload: dict) -> Lead:
        """Normalize an inbound WhatsApp webhook payload into a ``Lead``."""
        # TODO: map the real Cloud API webhook shape (entry/changes/messages).
        text = payload.get("text", "")
        sender = payload.get("from")
        return Lead(
            lead_id=str(uuid.uuid4()),
            channel=self.channel,
            customer_contact=sender,
            raw_text=text,
        )

    def poll(self) -> list[Lead]:
        # WhatsApp is push-based; polling is a no-op. Kept for interface parity.
        return []

    def send(self, to: str, message: str) -> None:
        # TODO: POST /{phone_id}/messages with a text body.
        self._http.post(
            f"/{self._phone_id}/messages",
            json={"messaging_product": "whatsapp", "to": to, "text": {"body": message}},
        )

"""Channel abstraction shared by WhatsApp / Email connectors.

A ``ChannelConnector`` both *receives* enquiries (as ``Lead``s) and *sends*
messages (quotations, negotiation notes) back out. Keeping this a Protocol lets
the orchestrator treat every channel uniformly.
"""
from __future__ import annotations

from typing import Protocol

from ..models import Channel, Lead


class ChannelConnector(Protocol):
    channel: Channel

    def poll(self) -> list[Lead]:
        """Fetch newly received enquiries as normalized leads."""
        ...

    def send(self, to: str, message: str) -> None:
        """Deliver an outbound message (quotation, negotiation, etc.)."""
        ...

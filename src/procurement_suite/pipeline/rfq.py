"""RFQ dispatch — fan a requirement out to multiple vendors.

Renders a request-for-quotation from the structured requirement and sends it to
each candidate vendor over their preferred channel.
"""
from __future__ import annotations

from ..models import Requirement


def render_rfq(requirement: Requirement) -> str:
    """Render a human-readable RFQ body from the structured requirement."""
    lines = "\n".join(
        f"  - {line.quantity} {line.unit} x {line.description}" for line in requirement.lines
    )
    return (
        "Request for Quotation\n"
        "We are sourcing the following items. Please share your best per-unit "
        "pricing and lead time:\n"
        f"{lines}\n"
    )


class RFQDispatcher:
    def __init__(self, senders: dict[str, object] | None = None) -> None:
        # vendor_id -> connector with a `.send(to, message)` method.
        self._senders = senders or {}

    def dispatch(self, requirement: Requirement, vendors: list[dict]) -> str:
        """Send the RFQ to each vendor; returns the rendered RFQ body."""
        body = render_rfq(requirement)
        for vendor in vendors:
            connector = self._senders.get(vendor["channel"])
            if connector is not None:
                connector.send(vendor["contact"], body)  # type: ignore[attr-defined]
        return body

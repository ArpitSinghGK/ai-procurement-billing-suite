"""Quote-extraction agent — the answer to *"vendors reply in different formats."*

Vendors respond over WhatsApp/email as free text, tables, PDFs pasted inline, or
half-structured lists. This agent normalizes any of those into ``QuoteLine``s so
the comparison engine sees one clean shape regardless of source.
"""
from __future__ import annotations

from ..models import QuoteLine, VendorQuote
from .client import LLMClient

_SYSTEM = (
    "You are a procurement analyst. A vendor has replied to a request for quotation "
    "in an arbitrary format (free text, a table, a forwarded message). Extract every "
    "priced line item into a normalized structure. Map obvious synonyms to the "
    "requested items. If a lead time is stated, capture it in days. Never guess a "
    "price that is not present — omit the line instead."
)

_SCHEMA = {
    "type": "object",
    "properties": {
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "integer"},
                    "unit_price": {"type": "number"},
                    "currency": {"type": "string"},
                    "lead_time_days": {"type": ["integer", "null"]},
                },
                "required": ["description", "quantity", "unit_price", "currency"],
                "additionalProperties": False,
            },
        },
        "notes": {"type": ["string", "null"]},
    },
    "required": ["lines"],
    "additionalProperties": False,
}


class QuoteExtractor:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    def extract(self, vendor_id: str, vendor_name: str, raw_reply: str) -> VendorQuote:
        data = self._llm.extract_json(
            system=_SYSTEM,
            user=f"Vendor reply:\n{raw_reply}",
            schema=_SCHEMA,
        )
        lines = [
            QuoteLine(
                description=line["description"],
                quantity=line["quantity"],
                unit_price=line["unit_price"],
                currency=line.get("currency", "INR"),
                lead_time_days=line.get("lead_time_days"),
            )
            for line in data["lines"]
        ]
        return VendorQuote(
            vendor_id=vendor_id,
            vendor_name=vendor_name,
            lines=lines,
            notes=data.get("notes"),
        )

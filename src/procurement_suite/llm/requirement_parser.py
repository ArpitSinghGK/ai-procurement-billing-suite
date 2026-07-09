"""Requirement-understanding agent.

Turns a free-text enquiry (``"Need CCTV 16 camera setup"``) into a structured
bill of materials — the line items the rest of the pipeline sources and prices.
"""
from __future__ import annotations

from ..models import Lead, Requirement, RequirementLine
from .client import LLMClient

_SYSTEM = (
    "You are a procurement solutions engineer. Given a customer enquiry, break it "
    "down into a concrete bill of materials: every distinct product or service the "
    "customer needs to fulfil the request, with sensible default quantities and "
    "units. Expand implied items (e.g. a CCTV setup implies cameras, an NVR, cabling, "
    "installation). Do not invent brands or prices."
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
                    "unit": {"type": "string"},
                    "specs": {"type": "object", "additionalProperties": {"type": "string"}},
                },
                "required": ["description", "quantity", "unit"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["lines"],
    "additionalProperties": False,
}


class RequirementParser:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    def parse(self, lead: Lead) -> Requirement:
        data = self._llm.extract_json(
            system=_SYSTEM,
            user=f"Enquiry:\n{lead.raw_text}",
            schema=_SCHEMA,
        )
        lines = [
            RequirementLine(
                description=line["description"],
                quantity=line["quantity"],
                unit=line["unit"],
                specs=line.get("specs", {}),
            )
            for line in data["lines"]
        ]
        return Requirement(lead=lead, lines=lines)

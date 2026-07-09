"""Auto-negotiation agent — drafts a *"can you beat this price?"* message.

Given the current L1 for an item and a vendor's standing quote, it produces a
polite, specific counter asking the vendor to improve their number. The message
is sent back through whichever channel the vendor uses.
"""
from __future__ import annotations

from .client import LLMClient

_SYSTEM = (
    "You draft short, professional procurement negotiation messages. Ask the vendor "
    "to beat a target price for a specific item. Be courteous, concrete about the "
    "quantity and target, and leave the door open for a counter-offer. One short "
    "paragraph, no preamble."
)


class Negotiator:
    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm or LLMClient()

    def draft(
        self,
        *,
        vendor_name: str,
        item: str,
        quantity: int,
        their_price: float,
        target_price: float,
        currency: str = "INR",
    ) -> str:
        user = (
            f"Vendor: {vendor_name}\nItem: {item}\nQuantity: {quantity}\n"
            f"Their quote: {currency} {their_price} / unit\n"
            f"Target (current L1): {currency} {target_price} / unit"
        )
        return self._llm.complete(system=_SYSTEM, user=user)

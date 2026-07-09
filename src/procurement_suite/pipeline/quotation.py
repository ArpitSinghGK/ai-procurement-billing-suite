"""Quotation builder — turn a comparison into a customer-facing quote.

Applies markup (overall or per-item) via the margin engine, totals the quote,
and stamps it with an id. The orchestrator then sends it to the customer and
pushes it to the ERP.
"""
from __future__ import annotations

import uuid

from ..models import ComparisonResult, Quotation
from ..services.markup import apply_markup


def build_quotation(
    comparison: ComparisonResult,
    *,
    overall_pct: float | None = None,
    per_item_pct: dict[str, float] | None = None,
) -> Quotation:
    lines = apply_markup(comparison, overall_pct=overall_pct, per_item_pct=per_item_pct)
    total = round(sum(line.sell_price for line in lines), 2)
    return Quotation(
        quotation_id=f"QTN-{uuid.uuid4().hex[:8].upper()}",
        lead_id=comparison.requirement.lead.lead_id,
        lines=lines,
        total=total,
    )


def render_quotation(quotation: Quotation) -> str:
    """Render a quotation as a message body for WhatsApp / email."""
    rows = "\n".join(
        f"  - {line.quantity} x {line.description}: {quotation.currency} {line.sell_price}"
        for line in quotation.lines
    )
    return (
        f"Quotation {quotation.quotation_id}\n{rows}\n"
        f"Total: {quotation.currency} {quotation.total}"
    )

"""Margin engine — apply markup overall or per line item.

Given the L1 cost of each line, produce the customer-facing sell price. Callers
can pass a single blanket markup or override it per line (by description).
"""
from __future__ import annotations

from ..config import get_settings
from ..models import ComparisonResult, QuotationLine


def apply_markup(
    comparison: ComparisonResult,
    *,
    overall_pct: float | None = None,
    per_item_pct: dict[str, float] | None = None,
) -> list[QuotationLine]:
    """Build quotation lines from a comparison, applying markup.

    Precedence per line: ``per_item_pct[description]`` > ``overall_pct`` >
    the configured ``DEFAULT_MARKUP_PCT``.
    """
    per_item_pct = per_item_pct or {}
    default_pct = overall_pct if overall_pct is not None else get_settings().default_markup_pct

    lines: list[QuotationLine] = []
    for line in comparison.lines:
        pct = per_item_pct.get(line.description, default_pct)
        cost = line.l1_unit_price * line.quantity
        sell = round(cost * (1 + pct), 2)
        lines.append(
            QuotationLine(
                description=line.description,
                quantity=line.quantity,
                cost_price=cost,
                markup_pct=pct,
                sell_price=sell,
            )
        )
    return lines

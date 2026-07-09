"""Procurement — raise purchase orders per vendor from the finalized comparison.

Once L1 is accepted, each winning vendor gets a PO covering the lines they won,
with a delivery timeline. Lines are grouped by their L1 source vendor.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, timedelta

from ..models import ComparisonResult, PurchaseOrder, QuoteLine


def build_purchase_orders(
    comparison: ComparisonResult,
    *,
    lead_time_days: int = 7,
) -> list[PurchaseOrder]:
    """Group won lines by vendor and emit one PO per vendor."""
    by_vendor: dict[str, list[QuoteLine]] = defaultdict(list)
    for line in comparison.lines:
        # Online-price sources are benchmarks, not purchasable vendors here.
        if line.l1_source.startswith("online:"):
            continue
        by_vendor[line.l1_source].append(
            QuoteLine(
                description=line.description,
                quantity=line.quantity,
                unit_price=line.l1_unit_price,
            )
        )

    required_by = date.today() + timedelta(days=lead_time_days)
    orders: list[PurchaseOrder] = []
    for vendor_id, lines in by_vendor.items():
        total = round(sum(ln.unit_price * ln.quantity for ln in lines), 2)
        orders.append(
            PurchaseOrder(
                po_id=f"PO-{uuid.uuid4().hex[:8].upper()}",
                vendor_id=vendor_id,
                lines=lines,
                required_by=required_by,
                total=total,
            )
        )
    return orders

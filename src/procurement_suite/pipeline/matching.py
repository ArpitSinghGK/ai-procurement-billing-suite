"""3-way matching — reconcile a vendor's purchase invoice against its PO.

On goods receipt, the vendor's invoice is checked line-by-line against the PO
that was placed. Any price or quantity drift, or a missing line, is flagged so
the discrepancy report can be actioned before payment.
"""
from __future__ import annotations

from ..models import MatchLine, MatchReport, MatchStatus, PurchaseOrder, VendorQuote

# Absolute tolerance (currency units) for treating amounts as equal.
_PRICE_TOLERANCE = 0.01


def three_way_match(
    po: PurchaseOrder,
    invoice: VendorQuote,
    invoice_id: str,
) -> MatchReport:
    """Compare invoice lines to PO lines and produce a match report."""
    invoice_by_desc = {ln.description.lower(): ln for ln in invoice.lines}
    match_lines: list[MatchLine] = []
    all_ok = True

    for po_line in po.lines:
        po_amount = round(po_line.unit_price * po_line.quantity, 2)
        inv = invoice_by_desc.get(po_line.description.lower())

        if inv is None:
            status = MatchStatus.MISSING
            inv_amount = 0.0
        else:
            inv_amount = round(inv.unit_price * inv.quantity, 2)
            if inv.quantity != po_line.quantity:
                status = MatchStatus.QTY_MISMATCH
            elif abs(inv_amount - po_amount) > _PRICE_TOLERANCE:
                status = MatchStatus.PRICE_MISMATCH
            else:
                status = MatchStatus.MATCHED

        if status is not MatchStatus.MATCHED:
            all_ok = False

        match_lines.append(
            MatchLine(
                description=po_line.description,
                status=status,
                po_amount=po_amount,
                invoice_amount=inv_amount,
            )
        )

    return MatchReport(
        po_id=po.po_id,
        vendor_invoice_id=invoice_id,
        lines=match_lines,
        ok=all_ok,
    )

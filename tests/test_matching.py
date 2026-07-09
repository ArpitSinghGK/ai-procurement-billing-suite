"""3-way matching — PO vs vendor purchase invoice."""
from __future__ import annotations

from datetime import date, timedelta

from procurement_suite.models import (
    MatchStatus,
    PurchaseOrder,
    QuoteLine,
    VendorQuote,
)
from procurement_suite.pipeline.matching import three_way_match


def _po() -> PurchaseOrder:
    return PurchaseOrder(
        po_id="PO-1",
        vendor_id="V2",
        lines=[
            QuoteLine(description="CCTV Camera", quantity=16, unit_price=1100),
            QuoteLine(description="NVR 16 channel", quantity=1, unit_price=9000),
        ],
        required_by=date.today() + timedelta(days=7),
        total=16 * 1100 + 9000,
    )


def test_clean_invoice_matches():
    invoice = VendorQuote(
        vendor_id="V2",
        vendor_name="Beta",
        lines=[
            QuoteLine(description="CCTV Camera", quantity=16, unit_price=1100),
            QuoteLine(description="NVR 16 channel", quantity=1, unit_price=9000),
        ],
    )
    report = three_way_match(_po(), invoice, invoice_id="VINV-1")

    assert report.ok is True
    assert all(ln.status is MatchStatus.MATCHED for ln in report.lines)


def test_price_and_missing_lines_are_flagged():
    invoice = VendorQuote(
        vendor_id="V2",
        vendor_name="Beta",
        lines=[
            QuoteLine(description="CCTV Camera", quantity=16, unit_price=1250),  # overcharge
            # NVR omitted from the invoice
        ],
    )
    report = three_way_match(_po(), invoice, invoice_id="VINV-2")

    by_desc = {ln.description: ln for ln in report.lines}
    assert report.ok is False
    assert by_desc["CCTV Camera"].status is MatchStatus.PRICE_MISMATCH
    assert by_desc["NVR 16 channel"].status is MatchStatus.MISSING

"""Billing — raise the customer invoice from the accepted quotation.

Mirrors the quotation (post-markup) into an invoice that is then pushed to the
ERP as the system of record.
"""
from __future__ import annotations

import uuid

from ..models import CustomerInvoice, Quotation


def build_customer_invoice(quotation: Quotation) -> CustomerInvoice:
    return CustomerInvoice(
        invoice_id=f"INV-{uuid.uuid4().hex[:8].upper()}",
        quotation_id=quotation.quotation_id,
        lines=quotation.lines,
        total=quotation.total,
    )

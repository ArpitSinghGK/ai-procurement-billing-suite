"""Domain models shared across the whole pipeline.

These Pydantic types are the contract every stage speaks — intake produces a
``Lead``, the requirement agent fills ``RequirementLine``s, vendors return
``VendorQuote``s, and comparison emits a ``ComparisonResult`` that feeds the
customer ``Quotation``, the vendor ``PurchaseOrder``s, and finally the
``CustomerInvoice``.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class Channel(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    MANUAL = "manual"


class Lead(BaseModel):
    """A raw enquiry captured from any intake channel."""

    lead_id: str
    channel: Channel
    customer_name: str | None = None
    customer_contact: str | None = None
    raw_text: str
    received_at: datetime = Field(default_factory=datetime.utcnow)


class RequirementLine(BaseModel):
    """One structured line item extracted from a free-text enquiry."""

    description: str
    quantity: int = 1
    unit: str = "nos"
    # ERP product id if the item resolved against the catalog, else None (new item).
    erp_product_id: str | None = None
    specs: dict[str, str] = Field(default_factory=dict)


class Requirement(BaseModel):
    """The fully-understood enquiry: a lead plus its structured BOM."""

    lead: Lead
    lines: list[RequirementLine]


class QuoteLine(BaseModel):
    """A single priced line inside a vendor quotation (already normalized)."""

    description: str
    quantity: int
    unit_price: float
    currency: str = "INR"
    lead_time_days: int | None = None


class VendorQuote(BaseModel):
    """A vendor's response to an RFQ, normalized from an arbitrary format."""

    vendor_id: str
    vendor_name: str
    lines: list[QuoteLine]
    # Free-form notes the extractor could not map to a structured field.
    notes: str | None = None


class PricedOption(BaseModel):
    """A candidate price for one requirement line from a single source."""

    source: str  # vendor id, or "online:<marketplace>"
    unit_price: float
    lead_time_days: int | None = None
    vendor_rating: float | None = None


class LineComparison(BaseModel):
    """L1 selection for one requirement line across all sourced options."""

    description: str
    quantity: int
    options: list[PricedOption]
    l1_source: str
    l1_unit_price: float


class ComparisonResult(BaseModel):
    """The full comparison across every requirement line."""

    requirement: Requirement
    lines: list[LineComparison]
    best_vendor_id: str | None = None


class QuotationLine(BaseModel):
    description: str
    quantity: int
    cost_price: float
    markup_pct: float
    sell_price: float


class Quotation(BaseModel):
    """Customer-facing quote with markup applied, ready to send + push to ERP."""

    quotation_id: str
    lead_id: str
    lines: list[QuotationLine]
    currency: str = "INR"
    total: float = 0.0
    erp_ref: str | None = None


class PurchaseOrder(BaseModel):
    """A PO to one vendor for the lines they won, with a delivery timeline."""

    po_id: str
    vendor_id: str
    lines: list[QuoteLine]
    required_by: date
    total: float = 0.0


class MatchStatus(str, Enum):
    MATCHED = "matched"
    PRICE_MISMATCH = "price_mismatch"
    QTY_MISMATCH = "qty_mismatch"
    MISSING = "missing"


class MatchLine(BaseModel):
    description: str
    status: MatchStatus
    po_amount: float
    invoice_amount: float


class MatchReport(BaseModel):
    """Result of 3-way matching a purchase invoice against its PO."""

    po_id: str
    vendor_invoice_id: str
    lines: list[MatchLine]
    ok: bool


class CustomerInvoice(BaseModel):
    """Final invoice raised to the end customer, mirrored into the ERP."""

    invoice_id: str
    quotation_id: str
    lines: list[QuotationLine]
    total: float
    erp_ref: str | None = None

"""FastAPI application exposing the procurement & billing pipeline.

Endpoints mirror the stages of the flow so the API surface reads like the
architecture. Business logic lives in the orchestrator; these handlers are thin.
"""
from __future__ import annotations

import uuid

from fastapi import FastAPI
from pydantic import BaseModel

from ..models import Channel, ComparisonResult, Lead, Requirement, VendorQuote
from ..orchestrator import ProcurementOrchestrator

app = FastAPI(
    title="AI Procurement & Billing Suite",
    version="0.1.0",
    summary="Enquiry to invoice: understand, source, compare (L1), quote, procure, match, bill.",
)

# A single shared orchestrator; collaborators default to real connectors.
orchestrator = ProcurementOrchestrator()


class EnquiryIn(BaseModel):
    channel: Channel = Channel.MANUAL
    customer_name: str | None = None
    customer_contact: str | None = None
    text: str


class VendorReplyIn(BaseModel):
    vendor_id: str
    vendor_name: str
    raw_reply: str


class QuoteRequestIn(BaseModel):
    comparison: ComparisonResult
    overall_markup_pct: float | None = None
    per_item_markup_pct: dict[str, float] | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/enquiries", response_model=Requirement)
def create_enquiry(enquiry: EnquiryIn) -> Requirement:
    """Stage 1-2: capture a lead and understand it into a structured BOM."""
    lead = Lead(
        lead_id=str(uuid.uuid4()),
        channel=enquiry.channel,
        customer_name=enquiry.customer_name,
        customer_contact=enquiry.customer_contact,
        raw_text=enquiry.text,
    )
    return orchestrator.understand(lead)


@app.post("/quotes/extract", response_model=VendorQuote)
def extract_quote(reply: VendorReplyIn) -> VendorQuote:
    """Stage 4: normalize a vendor reply (any format) into a structured quote."""
    return orchestrator.extract_quote(reply.vendor_id, reply.vendor_name, reply.raw_reply)


@app.post("/comparisons", response_model=ComparisonResult)
def compare(requirement: Requirement, quotes: list[VendorQuote]) -> ComparisonResult:
    """Stage 5: identify L1 and the best vendor across all sourced options."""
    return orchestrator.compare(requirement, quotes)


@app.post("/quotations")
def quote_customer(req: QuoteRequestIn) -> dict:
    """Stage 6: apply markup, build the customer quotation, push to ERP."""
    quotation = orchestrator.quote_customer(
        req.comparison,
        overall_pct=req.overall_markup_pct,
        per_item_pct=req.per_item_markup_pct,
    )
    return quotation.model_dump(mode="json")


def main() -> None:
    import uvicorn

    uvicorn.run("procurement_suite.api.app:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()

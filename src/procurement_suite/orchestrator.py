"""End-to-end orchestrator.

Ties every stage together so the architecture is visible in code, not just in
the diagram:

    Lead -> understand -> RFQ -> collect & extract quotes -> compare (L1)
         -> quote customer (markup) -> push to ERP -> POs -> 3-way match -> invoice

Each collaborator is injectable, so the pipeline is trivial to unit-test with
fakes and to run against real connectors in production.
"""
from __future__ import annotations

from .connectors.erp import ERPConnector
from .connectors.price_lookup import PriceLookup
from .llm.quote_extractor import QuoteExtractor
from .llm.requirement_parser import RequirementParser
from .models import (
    ComparisonResult,
    CustomerInvoice,
    Lead,
    PurchaseOrder,
    Quotation,
    Requirement,
    VendorQuote,
)
from .pipeline.billing import build_customer_invoice
from .pipeline.comparison import ComparisonEngine
from .pipeline.procurement import build_purchase_orders
from .pipeline.quotation import build_quotation
from .pipeline.rfq import RFQDispatcher, render_rfq
from .services.vendor_rating import VendorRatingStore


class ProcurementOrchestrator:
    def __init__(
        self,
        *,
        parser: RequirementParser | None = None,
        extractor: QuoteExtractor | None = None,
        comparator: ComparisonEngine | None = None,
        erp: ERPConnector | None = None,
        prices: PriceLookup | None = None,
        rfq: RFQDispatcher | None = None,
        ratings: VendorRatingStore | None = None,
    ) -> None:
        self._ratings = ratings or VendorRatingStore()
        self._parser = parser or RequirementParser()
        self._extractor = extractor or QuoteExtractor()
        self._comparator = comparator or ComparisonEngine(self._ratings)
        self._erp = erp
        self._prices = prices or PriceLookup()
        self._rfq = rfq or RFQDispatcher()

    # --- stage 1-2: capture + understand -------------------------------------
    def understand(self, lead: Lead) -> Requirement:
        return self._parser.parse(lead)

    # --- stage 3: dispatch RFQ ------------------------------------------------
    def dispatch_rfq(self, requirement: Requirement, vendors: list[dict]) -> str:
        return self._rfq.dispatch(requirement, vendors) if vendors else render_rfq(requirement)

    # --- stage 4-5: collect quotes + compare ---------------------------------
    def extract_quote(self, vendor_id: str, vendor_name: str, raw_reply: str) -> VendorQuote:
        return self._extractor.extract(vendor_id, vendor_name, raw_reply)

    def compare(
        self, requirement: Requirement, quotes: list[VendorQuote]
    ) -> ComparisonResult:
        online = {line.description: self._prices.lookup(line) for line in requirement.lines}
        return self._comparator.compare(requirement, quotes, online)

    # --- stage 6: quote the customer + push to ERP ---------------------------
    def quote_customer(
        self,
        comparison: ComparisonResult,
        *,
        overall_pct: float | None = None,
        per_item_pct: dict[str, float] | None = None,
    ) -> Quotation:
        quotation = build_quotation(
            comparison, overall_pct=overall_pct, per_item_pct=per_item_pct
        )
        if self._erp is not None:
            quotation.erp_ref = self._erp.push_quotation(quotation)
        return quotation

    # --- stage 7: procurement ------------------------------------------------
    def raise_purchase_orders(self, comparison: ComparisonResult) -> list[PurchaseOrder]:
        return build_purchase_orders(comparison)

    # --- stage 8: billing ----------------------------------------------------
    def invoice_customer(self, quotation: Quotation) -> CustomerInvoice:
        invoice = build_customer_invoice(quotation)
        if self._erp is not None:
            invoice.erp_ref = self._erp.push_invoice(invoice)
        return invoice

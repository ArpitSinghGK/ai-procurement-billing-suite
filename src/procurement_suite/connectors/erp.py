"""ERP connector.

The initial product catalog is fetched from the ERP; new products are created
when an enquiry references something not yet listed; finalized quotations and
customer invoices are pushed back. This is the system of record the suite wraps.
"""
from __future__ import annotations

import httpx

from ..config import get_settings
from ..models import CustomerInvoice, Quotation


class ERPConnector:
    def __init__(self) -> None:
        settings = get_settings()
        self._http = httpx.Client(
            base_url=settings.erp_base_url,
            headers={"Authorization": f"Bearer {settings.erp_api_key}"},
            timeout=30.0,
        )

    def fetch_catalog(self) -> list[dict]:
        """Return the product catalog used to resolve requirement lines."""
        # TODO: GET /products (paginated) and return normalized rows.
        resp = self._http.get("/products")
        resp.raise_for_status()
        return resp.json().get("products", [])

    def find_product(self, description: str) -> dict | None:
        """Look up a product by description; ``None`` if not in the catalog."""
        # TODO: GET /products?search=... — placeholder returns no match.
        return None

    def create_product(self, description: str, unit: str, specs: dict[str, str]) -> str:
        """Create a new product when the enquiry references an unlisted item."""
        resp = self._http.post(
            "/products",
            json={"description": description, "unit": unit, "specs": specs},
        )
        resp.raise_for_status()
        return resp.json()["product_id"]

    def push_quotation(self, quotation: Quotation) -> str:
        """Push a finalized quotation to the ERP; return its ERP reference."""
        resp = self._http.post("/quotations", json=quotation.model_dump(mode="json"))
        resp.raise_for_status()
        return resp.json()["erp_ref"]

    def push_invoice(self, invoice: CustomerInvoice) -> str:
        """Push the customer invoice to the ERP; return its ERP reference."""
        resp = self._http.post("/invoices", json=invoice.model_dump(mode="json"))
        resp.raise_for_status()
        return resp.json()["erp_ref"]

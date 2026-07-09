"""Vendor rating.

A 0–5 score per vendor, combining price competitiveness, on-time delivery, and
quality history. The comparison engine uses it to break ties and to surface the
"best vendor" alongside the strict L1 (lowest price).
"""
from __future__ import annotations


class VendorRatingStore:
    def __init__(self, ratings: dict[str, float] | None = None) -> None:
        # In production this is backed by delivery/quality history in the ERP/DB.
        self._ratings = ratings or {}

    def get(self, vendor_id: str, default: float = 3.0) -> float:
        return self._ratings.get(vendor_id, default)

    def set(self, vendor_id: str, rating: float) -> None:
        self._ratings[vendor_id] = max(0.0, min(5.0, rating))

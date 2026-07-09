"""Comparison engine — identify L1 (lowest price) and the best vendor.

Consumes the normalized vendor quotes plus any online price options, and for
each requirement line selects the L1 source. A rating-weighted tally across all
lines surfaces the overall "best vendor".
"""
from __future__ import annotations

from collections import defaultdict

from ..models import (
    ComparisonResult,
    LineComparison,
    PricedOption,
    Requirement,
    VendorQuote,
)
from ..services.vendor_rating import VendorRatingStore


def _match(line_desc: str, quote_desc: str) -> bool:
    """Loose description match between a requirement line and a quote line."""
    a, b = line_desc.lower(), quote_desc.lower()
    return a in b or b in a


class ComparisonEngine:
    def __init__(self, ratings: VendorRatingStore | None = None) -> None:
        self._ratings = ratings or VendorRatingStore()

    def compare(
        self,
        requirement: Requirement,
        vendor_quotes: list[VendorQuote],
        online_options: dict[str, list[PricedOption]] | None = None,
    ) -> ComparisonResult:
        online_options = online_options or {}
        line_comparisons: list[LineComparison] = []
        # Track how often each vendor wins a line, weighted by rating.
        vendor_wins: dict[str, float] = defaultdict(float)

        for line in requirement.lines:
            options: list[PricedOption] = []

            for quote in vendor_quotes:
                for ql in quote.lines:
                    if _match(line.description, ql.description):
                        options.append(
                            PricedOption(
                                source=quote.vendor_id,
                                unit_price=ql.unit_price,
                                lead_time_days=ql.lead_time_days,
                                vendor_rating=self._ratings.get(quote.vendor_id),
                            )
                        )

            options.extend(online_options.get(line.description, []))

            if not options:
                continue

            # L1 = strictly lowest unit price; ties broken by higher vendor rating.
            l1 = min(options, key=lambda o: (o.unit_price, -(o.vendor_rating or 0)))
            line_comparisons.append(
                LineComparison(
                    description=line.description,
                    quantity=line.quantity,
                    options=options,
                    l1_source=l1.source,
                    l1_unit_price=l1.unit_price,
                )
            )
            vendor_wins[l1.source] += (l1.vendor_rating or 1.0)

        best_vendor = max(vendor_wins, key=vendor_wins.get) if vendor_wins else None
        return ComparisonResult(
            requirement=requirement,
            lines=line_comparisons,
            best_vendor_id=best_vendor,
        )

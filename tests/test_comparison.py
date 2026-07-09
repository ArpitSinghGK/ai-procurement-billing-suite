"""L1 selection and best-vendor logic."""
from __future__ import annotations

from procurement_suite.models import QuoteLine, VendorQuote
from procurement_suite.pipeline.comparison import ComparisonEngine
from procurement_suite.services.vendor_rating import VendorRatingStore


def test_l1_picks_lowest_price_per_line(cctv_requirement):
    quotes = [
        VendorQuote(
            vendor_id="V1",
            vendor_name="Alpha",
            lines=[
                QuoteLine(description="CCTV Camera", quantity=16, unit_price=1200),
                QuoteLine(description="NVR 16 channel", quantity=1, unit_price=9000),
            ],
        ),
        VendorQuote(
            vendor_id="V2",
            vendor_name="Beta",
            lines=[
                QuoteLine(description="CCTV Camera", quantity=16, unit_price=1100),
                QuoteLine(description="NVR 16 channel", quantity=1, unit_price=9500),
            ],
        ),
    ]

    result = ComparisonEngine().compare(cctv_requirement, quotes)

    by_desc = {line.description: line for line in result.lines}
    assert by_desc["CCTV Camera"].l1_source == "V2"  # 1100 < 1200
    assert by_desc["CCTV Camera"].l1_unit_price == 1100
    assert by_desc["NVR 16 channel"].l1_source == "V1"  # 9000 < 9500


def test_ties_broken_by_higher_rating(cctv_requirement):
    quotes = [
        VendorQuote(
            vendor_id="V1",
            vendor_name="Alpha",
            lines=[QuoteLine(description="CCTV Camera", quantity=16, unit_price=1000)],
        ),
        VendorQuote(
            vendor_id="V2",
            vendor_name="Beta",
            lines=[QuoteLine(description="CCTV Camera", quantity=16, unit_price=1000)],
        ),
    ]
    ratings = VendorRatingStore({"V1": 3.0, "V2": 4.5})

    result = ComparisonEngine(ratings).compare(cctv_requirement, quotes)

    assert result.lines[0].l1_source == "V2"  # equal price -> higher rating wins
    assert result.best_vendor_id == "V2"

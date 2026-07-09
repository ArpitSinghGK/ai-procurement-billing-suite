"""Markup engine — overall and per-item."""
from __future__ import annotations

from procurement_suite.models import (
    ComparisonResult,
    LineComparison,
    PricedOption,
    Requirement,
)
from procurement_suite.services.markup import apply_markup


def _comparison(requirement: Requirement) -> ComparisonResult:
    return ComparisonResult(
        requirement=requirement,
        lines=[
            LineComparison(
                description="CCTV Camera",
                quantity=16,
                options=[PricedOption(source="V2", unit_price=1100)],
                l1_source="V2",
                l1_unit_price=1100,
            ),
            LineComparison(
                description="NVR 16 channel",
                quantity=1,
                options=[PricedOption(source="V1", unit_price=9000)],
                l1_source="V1",
                l1_unit_price=9000,
            ),
        ],
    )


def test_overall_markup(cctv_requirement):
    lines = apply_markup(_comparison(cctv_requirement), overall_pct=0.10)

    camera = next(ln for ln in lines if ln.description == "CCTV Camera")
    assert camera.cost_price == 1100 * 16
    assert camera.sell_price == round(1100 * 16 * 1.10, 2)
    assert all(ln.markup_pct == 0.10 for ln in lines)


def test_per_item_markup_overrides_overall(cctv_requirement):
    lines = apply_markup(
        _comparison(cctv_requirement),
        overall_pct=0.10,
        per_item_pct={"NVR 16 channel": 0.25},
    )

    nvr = next(ln for ln in lines if ln.description == "NVR 16 channel")
    camera = next(ln for ln in lines if ln.description == "CCTV Camera")
    assert nvr.markup_pct == 0.25
    assert nvr.sell_price == round(9000 * 1.25, 2)
    assert camera.markup_pct == 0.10  # unchanged by the per-item override

"""Shared fixtures — a small CCTV enquiry mirroring the classic use case."""
from __future__ import annotations

import pytest

from procurement_suite.models import Channel, Lead, Requirement, RequirementLine


@pytest.fixture
def cctv_requirement() -> Requirement:
    lead = Lead(lead_id="L1", channel=Channel.MANUAL, raw_text="Need CCTV 16 camera setup")
    return Requirement(
        lead=lead,
        lines=[
            RequirementLine(description="CCTV Camera", quantity=16, unit="nos"),
            RequirementLine(description="NVR 16 channel", quantity=1, unit="nos"),
        ],
    )

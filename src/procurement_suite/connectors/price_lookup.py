"""Online price lookup.

Fetches current market/marketplace prices for a requirement line so they can be
folded into the comparison alongside vendor quotes — giving the buyer a live
benchmark even before vendors reply.
"""
from __future__ import annotations

from ..models import PricedOption, RequirementLine


class PriceLookup:
    """Returns market-price options for a requirement line.

    A production build wires this to a marketplace API or a Claude web-search
    tool call; the interface below is what the comparison engine consumes.
    """

    def lookup(self, line: RequirementLine) -> list[PricedOption]:
        # TODO: query marketplace API / web search and normalize hits.
        return []

"""Thin wrapper around the Anthropic SDK.

Centralizes model selection, adaptive thinking, and JSON structured-output
plumbing so the individual agents stay declarative. All calls go through
``extract_json`` (schema-constrained) or ``complete`` (free text).
"""
from __future__ import annotations

import json
from typing import Any

import anthropic

from ..config import get_settings


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        settings = get_settings()
        self._client = anthropic.Anthropic(api_key=api_key or settings.anthropic_api_key)
        self._model = model or settings.llm_model

    def extract_json(
        self,
        *,
        system: str,
        user: str,
        schema: dict[str, Any],
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Run a schema-constrained extraction and return parsed JSON.

        Uses ``output_config.format`` (structured outputs) so the response is
        guaranteed to satisfy ``schema`` — the backbone of turning messy vendor
        replies into normalized quotes.
        """
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": schema}},
        )
        text = next(b.text for b in response.content if b.type == "text")
        return json.loads(text)

    def complete(self, *, system: str, user: str, max_tokens: int = 1024) -> str:
        """Free-text completion (e.g. drafting a negotiation message)."""
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            thinking={"type": "adaptive"},
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in response.content if b.type == "text")

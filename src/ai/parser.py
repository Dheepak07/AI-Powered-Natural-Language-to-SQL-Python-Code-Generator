"""
src/ai/parser.py
Parses and validates the structured JSON output from the AI chain.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from src.utils.logger import get_logger

logger = get_logger("ai.parser")

VALID_CHART_TYPES = {"bar", "line", "pie", "scatter", "table", "heatmap"}


@dataclass
class VisualizationInfo:
    chart_type: str = "table"
    x_axis: str = ""
    y_axis: str = ""
    rationale: str = ""


@dataclass
class AIResponse:
    sql: str = ""
    pandas_code: str = ""
    explanation: str = ""
    visualization: VisualizationInfo = field(default_factory=VisualizationInfo)
    raw_response: str = ""
    parse_error: str = ""

    @property
    def is_valid(self) -> bool:
        return bool(self.sql and self.explanation and not self.parse_error)


def parse_ai_response(raw: str) -> AIResponse:
    """
    Extract and validate the structured JSON from the AI's response.

    Handles:
    - Pure JSON responses
    - JSON wrapped in markdown code fences
    - Partially malformed JSON (best-effort extraction)
    """
    resp = AIResponse(raw_response=raw)

    # Strip markdown fences if present
    cleaned = _strip_fences(raw)

    data = _try_parse_json(cleaned)
    if data is None:
        resp.parse_error = "Could not extract valid JSON from AI response."
        logger.error("JSON parse failed. Raw response (first 500): %s", raw[:500])
        return resp

    resp.sql = _safe_str(data.get("sql", "")).strip()
    resp.pandas_code = _safe_str(data.get("pandas_code", "")).strip()
    resp.explanation = _safe_str(data.get("explanation", "")).strip()

    viz_raw = data.get("visualization", {})
    if isinstance(viz_raw, dict):
        chart_type = _safe_str(viz_raw.get("chart_type", "table")).lower()
        if chart_type not in VALID_CHART_TYPES:
            logger.warning("Unknown chart type '%s', defaulting to 'table'.", chart_type)
            chart_type = "table"
        resp.visualization = VisualizationInfo(
            chart_type=chart_type,
            x_axis=_safe_str(viz_raw.get("x_axis", "")),
            y_axis=_safe_str(viz_raw.get("y_axis", "")),
            rationale=_safe_str(viz_raw.get("rationale", "")),
        )

    if not resp.sql:
        resp.parse_error = "AI response did not contain a SQL query."

    return resp


# ── Helpers ───────────────────────────────────────────────────────────────────

def _strip_fences(text: str) -> str:
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*", "", text)
    return text.strip()


def _try_parse_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try to extract embedded JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None


def _safe_str(val: Any) -> str:
    return str(val) if val is not None else ""

"""
tests/test_chain.py
Unit tests for the AI response parser (no live API calls needed).
Run: pytest tests/test_chain.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from src.ai.parser import parse_ai_response, AIResponse


def _make_raw(overrides: dict = None) -> str:
    base = {
        "sql": "SELECT customer_id, SUM(unit_price) AS revenue FROM order_items GROUP BY customer_id ORDER BY revenue DESC LIMIT 10",
        "pandas_code": "result = df.groupby('customer_id')['unit_price'].sum().sort_values(ascending=False).head(10)",
        "explanation": "This query sums unit prices per customer and returns the top 10 by revenue.",
        "visualization": {
            "chart_type": "bar",
            "x_axis": "customer_id",
            "y_axis": "revenue",
            "rationale": "A bar chart clearly compares revenue across discrete customer IDs.",
        },
    }
    if overrides:
        base.update(overrides)
    return json.dumps(base)


class TestParseValidResponse:
    def test_parses_sql(self):
        resp = parse_ai_response(_make_raw())
        assert "SELECT" in resp.sql.upper()

    def test_parses_pandas(self):
        resp = parse_ai_response(_make_raw())
        assert "groupby" in resp.pandas_code

    def test_parses_explanation(self):
        resp = parse_ai_response(_make_raw())
        assert len(resp.explanation) > 10

    def test_parses_visualization(self):
        resp = parse_ai_response(_make_raw())
        assert resp.visualization.chart_type == "bar"
        assert resp.visualization.x_axis == "customer_id"

    def test_is_valid(self):
        resp = parse_ai_response(_make_raw())
        assert resp.is_valid


class TestParseWithFences:
    def test_strips_json_fences(self):
        raw = "```json\n" + _make_raw() + "\n```"
        resp = parse_ai_response(raw)
        assert resp.is_valid

    def test_strips_plain_fences(self):
        raw = "```\n" + _make_raw() + "\n```"
        resp = parse_ai_response(raw)
        assert resp.is_valid


class TestInvalidChartType:
    def test_defaults_unknown_chart_type(self):
        raw = _make_raw({"visualization": {"chart_type": "donut", "x_axis": "x", "y_axis": "y", "rationale": "test"}})
        resp = parse_ai_response(raw)
        assert resp.visualization.chart_type == "table"


class TestMalformedResponse:
    def test_empty_string(self):
        resp = parse_ai_response("")
        assert not resp.is_valid
        assert resp.parse_error

    def test_plain_text(self):
        resp = parse_ai_response("Here is your SQL: SELECT 1")
        assert not resp.is_valid

    def test_missing_sql_key(self):
        raw = json.dumps({"explanation": "test", "pandas_code": "x=1", "visualization": {}})
        resp = parse_ai_response(raw)
        assert not resp.is_valid

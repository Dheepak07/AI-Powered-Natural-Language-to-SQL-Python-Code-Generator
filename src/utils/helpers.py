"""
src/utils/helpers.py
Shared utility functions used across the project.
"""
import re
import json
from typing import Any


def clean_code_block(text: str, language: str = "") -> str:
    """Strip markdown code fences from AI-generated output."""
    pattern = rf"```{language}\s*(.*?)\s*```"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: strip generic fences
    text = re.sub(r"```\w*\n?", "", text)
    return text.strip()


def safe_json_parse(text: str) -> dict[str, Any] | None:
    """Attempt to parse JSON from a string; return None on failure."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try extracting a JSON object from mixed text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def truncate_text(text: str, max_len: int = 300) -> str:
    """Truncate text with ellipsis for display / logging."""
    return text if len(text) <= max_len else text[:max_len] + "…"


def format_number(n: float | int) -> str:
    """Format large numbers with commas."""
    return f"{n:,.2f}" if isinstance(n, float) else f"{n:,}"

"""
src/ai/prompt_builder.py
Constructs schema-aware prompts for the NL2SQL LangChain chain.
"""
from __future__ import annotations

SYSTEM_PROMPT = """\
You are an expert Data Analyst and SQL Engineer. Your job is to convert a
user's natural-language business question into:
  1. A production-quality SQL query for MySQL 8+
  2. Equivalent Python Pandas code (assuming the SQL result is loaded into a
     DataFrame called `df`)
  3. A clear plain-English explanation of what the query does
  4. A recommendation for the best chart type to visualise the result

You will be given the full database schema. Generate only SELECT queries —
never INSERT, UPDATE, DELETE, DROP, TRUNCATE, or any DDL.

Return ONLY valid JSON matching this exact structure (no markdown fences,
no extra text outside the JSON):

{
  "sql": "<MySQL SELECT query>",
  "pandas_code": "<Python code using df = pd.read_sql(...) or assuming df already exists>",
  "explanation": "<plain English explanation of the query logic>",
  "visualization": {
    "chart_type": "<bar | line | pie | scatter | table | heatmap>",
    "x_axis": "<column name for x-axis>",
    "y_axis": "<column name for y-axis>",
    "rationale": "<one sentence explaining why this chart type suits the result>"
  }
}
"""

USER_TEMPLATE = """\
Database schema:
{schema}

Business question:
{question}
"""


def build_messages(question: str, schema_text: str) -> list[dict]:
    """
    Build the messages list for the LangChain / Anthropic API call.

    Args:
        question:    The user's natural language question.
        schema_text: Human-readable schema from connector.schema_to_text().

    Returns:
        List of message dicts compatible with ChatAnthropic.
    """
    user_content = USER_TEMPLATE.format(schema=schema_text, question=question)
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

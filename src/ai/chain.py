"""
src/ai/chain.py
LangChain chain that calls Anthropic Claude and returns a parsed AIResponse.
"""
from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import settings
from src.ai.prompt_builder import SYSTEM_PROMPT, USER_TEMPLATE
from src.ai.parser import AIResponse, parse_ai_response
from src.db.connector import get_schema_info, schema_to_text
from src.utils.logger import get_logger

logger = get_logger("ai.chain")


class NL2SQLChain:
    """
    Orchestrates the full NL → SQL pipeline:
    1. Introspects the live DB schema
    2. Builds a schema-aware prompt
    3. Calls Claude via LangChain
    4. Parses the structured JSON response
    """

    def __init__(self):
        if not settings.ANTHROPIC_API_KEY:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env file."
            )
        self._llm = ChatAnthropic(
            model=settings.MODEL_NAME,
            api_key=settings.ANTHROPIC_API_KEY,
            max_tokens=settings.MAX_TOKENS,
            temperature=settings.TEMPERATURE,
        )
        self._schema_text: str = ""
        self._schema_tables: set[str] = set()

    # ── Schema (cached per session) ───────────────────────────────────────────

    def refresh_schema(self) -> None:
        """Reload schema from the live database."""
        schema_info = get_schema_info()
        self._schema_text = schema_to_text(schema_info)
        self._schema_tables = set(schema_info.keys())
        logger.info("Schema refreshed: %d tables.", len(self._schema_tables))

    @property
    def schema_text(self) -> str:
        if not self._schema_text:
            self.refresh_schema()
        return self._schema_text

    @property
    def schema_tables(self) -> set[str]:
        if not self._schema_tables:
            self.refresh_schema()
        return self._schema_tables

    # ── Main entry point ─────────────────────────────────────────────────────

    def run(self, question: str) -> AIResponse:
        """
        Convert a natural language question to SQL + Pandas + explanation.

        Args:
            question: The user's business question in plain English.

        Returns:
            AIResponse dataclass with sql, pandas_code, explanation,
            visualization, and parse diagnostics.
        """
        logger.info("Processing question: %s", question)

        user_content = USER_TEMPLATE.format(
            schema=self.schema_text,
            question=question,
        )

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_content),
        ]

        try:
            response = self._llm.invoke(messages)
            raw_text = response.content
            logger.debug("Raw AI response: %s", raw_text[:300])
        except Exception as exc:  # noqa: BLE001
            logger.error("LLM call failed: %s", exc)
            result = AIResponse()
            result.parse_error = f"AI call failed: {exc}"
            return result

        parsed = parse_ai_response(raw_text)
        logger.info(
            "Parsed response — SQL: %s chars, valid: %s",
            len(parsed.sql),
            parsed.is_valid,
        )
        return parsed

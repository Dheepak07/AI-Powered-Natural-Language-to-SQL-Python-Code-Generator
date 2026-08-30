"""
src/validation/sql_validator.py
Multi-layer SQL safety and schema validation.
"""
from __future__ import annotations

import re
import sqlparse
from dataclasses import dataclass

from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("validation.sql")


@dataclass
class ValidationResult:
    valid: bool
    cleaned_sql: str = ""
    errors: list[str] = None
    warnings: list[str] = None

    def __post_init__(self):
        self.errors = self.errors or []
        self.warnings = self.warnings or []

    @property
    def error_summary(self) -> str:
        return " | ".join(self.errors)


class SQLValidator:
    """
    Multi-stage SQL validation pipeline.

    Stages
    ------
    1. Keyword blocklist  – reject write / DDL / admin keywords
    2. Statement type     – allow SELECT only (plus WITH for CTEs)
    3. sqlparse parse     – verify it is parseable SQL
    4. Schema check       – warn if referenced tables are not in the schema
    """

    def __init__(self, known_tables: set[str] | None = None):
        self.known_tables = known_tables or set()
        self.blocked = {kw.upper() for kw in settings.BLOCKED_KEYWORDS}

    # ── Public ───────────────────────────────────────────────────────────────

    def validate(self, sql: str, schema_tables: set[str] | None = None) -> ValidationResult:
        """Run all validation stages and return a ValidationResult."""
        tables = schema_tables or self.known_tables
        errors: list[str] = []
        warnings: list[str] = []

        # Stage 1: blocklist
        blocked_found = self._check_blocklist(sql)
        if blocked_found:
            errors.append(f"Blocked keywords detected: {', '.join(blocked_found)}")

        # Stage 2: statement type
        if not self._is_select(sql):
            errors.append("Only SELECT statements are permitted.")

        # Stage 3: parseability
        parse_ok, parse_err = self._check_parseable(sql)
        if not parse_ok:
            errors.append(f"SQL parse error: {parse_err}")

        # Stage 4: schema check (soft warnings)
        if tables:
            unknown = self._check_tables(sql, tables)
            if unknown:
                warnings.append(f"Unknown tables referenced: {', '.join(unknown)}")

        if errors:
            logger.warning("SQL validation failed: %s", " | ".join(errors))
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        cleaned = self._clean_sql(sql)
        logger.info("SQL passed validation. Warnings: %s", warnings or "none")
        return ValidationResult(valid=True, cleaned_sql=cleaned, warnings=warnings)

    # ── Private ──────────────────────────────────────────────────────────────

    def _check_blocklist(self, sql: str) -> list[str]:
        tokens = re.findall(r"\b[A-Za-z_]+\b", sql)
        return [t.upper() for t in tokens if t.upper() in self.blocked]

    def _is_select(self, sql: str) -> bool:
        stripped = sql.strip().upper()
        return stripped.startswith("SELECT") or stripped.startswith("WITH")

    def _check_parseable(self, sql: str) -> tuple[bool, str]:
        try:
            parsed = sqlparse.parse(sql)
            if not parsed or not parsed[0].tokens:
                return False, "Empty or unrecognised SQL."
            return True, ""
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)

    def _check_tables(self, sql: str, known: set[str]) -> list[str]:
        """Extract table names from FROM/JOIN clauses and check against schema."""
        # Simple regex extraction — good enough for most generated SQL
        pattern = r"\b(?:FROM|JOIN)\s+`?(\w+)`?"
        referenced = {m.group(1).lower() for m in re.finditer(pattern, sql, re.IGNORECASE)}
        return [t for t in referenced if t not in {k.lower() for k in known}]

    def _clean_sql(self, sql: str) -> str:
        """Normalise whitespace and remove trailing semicolons."""
        sql = sql.strip().rstrip(";").strip()
        # Collapse multiple spaces / newlines for readability
        sql = re.sub(r"\s+", " ", sql)
        return sql

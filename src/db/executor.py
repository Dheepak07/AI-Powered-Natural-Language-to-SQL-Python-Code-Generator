"""
src/db/executor.py
Safe query execution and result formatting.
"""
from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from src.db.connector import get_engine
from src.utils.logger import get_logger
from config.settings import settings

logger = get_logger("db.executor")


class QueryResult:
    """Container for SQL execution output."""

    def __init__(
        self,
        success: bool,
        data: pd.DataFrame | None = None,
        error: str | None = None,
        rows_returned: int = 0,
        execution_time_ms: float = 0.0,
    ):
        self.success = success
        self.data = data
        self.error = error
        self.rows_returned = rows_returned
        self.execution_time_ms = execution_time_ms

    def __repr__(self) -> str:
        if self.success:
            return f"<QueryResult rows={self.rows_returned} time={self.execution_time_ms:.1f}ms>"
        return f"<QueryResult ERROR={self.error}>"


def execute_query(sql: str) -> QueryResult:
    """
    Execute a read-only SQL query and return results as a QueryResult.

    Args:
        sql: A validated SELECT query string.

    Returns:
        QueryResult with DataFrame on success, error message on failure.
    """
    import time

    engine = get_engine()
    logger.info("Executing SQL: %s", sql[:200])

    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            rows = result.fetchmany(settings.MAX_ROWS_RETURNED)
            columns = list(result.keys())

        elapsed_ms = (time.perf_counter() - start) * 1000
        df = pd.DataFrame(rows, columns=columns)

        logger.info(
            "Query returned %d rows in %.1f ms.", len(df), elapsed_ms
        )
        return QueryResult(
            success=True,
            data=df,
            rows_returned=len(df),
            execution_time_ms=elapsed_ms,
        )

    except SQLAlchemyError as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.error("SQL execution error: %s", exc)
        return QueryResult(
            success=False,
            error=str(exc),
            execution_time_ms=elapsed_ms,
        )


def execute_pandas_code(code: str, df: pd.DataFrame | None = None) -> tuple[bool, object, str]:
    """
    Execute AI-generated Pandas code in a sandboxed local scope.

    Args:
        code:  Python Pandas code string.
        df:    Optional pre-loaded DataFrame (e.g. from prior SQL execution).

    Returns:
        Tuple of (success: bool, result: Any, error: str)
    """
    local_scope: dict = {"pd": pd}
    if df is not None:
        local_scope["df"] = df

    try:
        exec(code, {"__builtins__": {}}, local_scope)  # noqa: S102
        result = local_scope.get("result", local_scope.get("df"))
        return True, result, ""
    except Exception as exc:  # noqa: BLE001
        logger.error("Pandas execution error: %s", exc)
        return False, None, str(exc)

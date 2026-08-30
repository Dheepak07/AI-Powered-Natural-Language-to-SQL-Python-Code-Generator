"""
src/db/connector.py
SQLAlchemy connection pool for MySQL.
"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from config.settings import settings
from src.utils.logger import get_logger

logger = get_logger("db.connector")

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return a singleton SQLAlchemy engine with connection pooling."""
    global _engine
    if _engine is None:
        logger.info("Creating MySQL engine → %s:%s/%s",
                    settings.DB_HOST, settings.DB_PORT, settings.DB_NAME)
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,          # test connections before use
            pool_recycle=1800,           # recycle connections every 30 min
            echo=False,
        )
    return _engine


def test_connection() -> bool:
    """Verify that the database is reachable. Returns True/False."""
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful.")
        return True
    except SQLAlchemyError as exc:
        logger.error("Database connection failed: %s", exc)
        return False


def get_schema_info() -> dict:
    """
    Introspect the database and return a structured schema description.
    Used by the prompt builder to make AI queries schema-aware.
    """
    engine = get_engine()
    insp = inspect(engine)
    schema: dict = {}

    for table_name in insp.get_table_names():
        columns = []
        for col in insp.get_columns(table_name):
            columns.append({
                "name": col["name"],
                "type": str(col["type"]),
                "nullable": col.get("nullable", True),
            })
        fks = [
            {
                "column": fk["constrained_columns"],
                "references": f"{fk['referred_table']}.{fk['referred_columns']}",
            }
            for fk in insp.get_foreign_keys(table_name)
        ]
        schema[table_name] = {"columns": columns, "foreign_keys": fks}

    logger.debug("Schema introspected: %d tables found.", len(schema))
    return schema


def schema_to_text(schema: dict) -> str:
    """Convert the schema dict to a concise text representation for prompts."""
    lines = []
    for table, info in schema.items():
        col_defs = ", ".join(
            f"{c['name']} ({c['type']})" for c in info["columns"]
        )
        lines.append(f"Table `{table}`: {col_defs}")
        for fk in info.get("foreign_keys", []):
            lines.append(f"  FK: {fk['column']} → {fk['references']}")
    return "\n".join(lines)

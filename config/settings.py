"""
config/settings.py
Centralised configuration loaded from environment variables.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ── AI ──────────────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    MODEL_NAME: str = "claude-sonnet-4-6"
    MAX_TOKENS: int = 2048
    TEMPERATURE: float = 0.0  # deterministic for code generation

    # ── Database ─────────────────────────────────────────────────────────────
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", 3306))
    DB_NAME: str = os.getenv("DB_NAME", "ecommerce_db")
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ── App behaviour ────────────────────────────────────────────────────────
    MAX_ROWS_RETURNED: int = int(os.getenv("MAX_ROWS_RETURNED", 500))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = "logs"

    # ── SQL safety ───────────────────────────────────────────────────────────
    BLOCKED_KEYWORDS: list = [
        "DROP", "TRUNCATE", "DELETE", "INSERT", "UPDATE",
        "ALTER", "CREATE", "GRANT", "REVOKE", "EXEC",
    ]


settings = Settings()

"""Runtime configuration for the SpaceX S-1 monitor."""

from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_SEARCH_TERMS = (
    "Space Exploration Technologies",
    "Space Exploration Technologies Corp",
    "SpaceX",
)

DEFAULT_FORM_TYPES = ("S-1", "S-1/A", "DRS", "DRS/A")
DEFAULT_VALIDATION_TERMS = (
    "SpaceX",
    "Space Exploration Technologies",
)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str | None
    telegram_chat_id: str | None
    sec_user_agent: str
    db_path: str
    dry_run: bool
    timeout_seconds: float
    search_terms: tuple[str, ...]
    validation_terms: tuple[str, ...]
    alert_title: str
    form_types: tuple[str, ...]
    max_results_per_query: int

    @classmethod
    def from_env(cls) -> "Settings":
        test_query = os.getenv("TEST_QUERY")
        search_terms = (test_query,) if test_query else DEFAULT_SEARCH_TERMS
        validation_terms = (test_query,) if test_query else DEFAULT_VALIDATION_TERMS
        alert_title = "SEC FILING TEST ALERT" if test_query else "SPACEX S-1 ALERT"

        form_types = tuple(
            item.strip()
            for item in os.getenv("FORM_TYPES", ",".join(DEFAULT_FORM_TYPES)).split(",")
            if item.strip()
        )

        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            sec_user_agent=os.getenv("SEC_USER_AGENT")
            or "SpaceX-S1-Monitor contact@example.com",
            db_path=os.getenv("DB_PATH", "notifications.db"),
            dry_run=_env_bool("DRY_RUN", False),
            timeout_seconds=float(os.getenv("HTTP_TIMEOUT_SECONDS", "10")),
            search_terms=search_terms,
            validation_terms=validation_terms,
            alert_title=alert_title,
            form_types=form_types,
            max_results_per_query=int(os.getenv("MAX_RESULTS_PER_QUERY", "25")),
        )

    def validate_for_notifications(self) -> None:
        if self.dry_run:
            return
        missing = []
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.telegram_chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        if missing:
            joined = ", ".join(missing)
            raise RuntimeError(f"Missing required environment variable(s): {joined}")

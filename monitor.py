"""CLI entrypoint for the SpaceX S-1 monitor."""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from config import Settings
from db import NotificationStore
from notifiers.telegram import build_alert_message, send_telegram_message
from sources.sec_edgar import FilingEvent, search_sec_edgar


LOGGER = logging.getLogger(__name__)
ET = ZoneInfo("America/New_York")


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = Settings.from_env()

    try:
        settings.validate_for_notifications()
        store = NotificationStore(settings.db_path)
        events = search_sec_edgar(
            search_terms=settings.search_terms,
            form_types=settings.form_types,
            user_agent=settings.sec_user_agent,
            timeout_seconds=settings.timeout_seconds,
            max_results_per_query=settings.max_results_per_query,
            validation_terms=settings.validation_terms,
        )
        LOGGER.info("Found %s validated filing event(s)", len(events))
        notify_new_events(events, store, settings)
        LOGGER.info("Notification DB row count: %s", store.count())
        return 0
    except Exception:
        LOGGER.exception("Monitor run failed")
        return 1


def notify_new_events(
    events: list[FilingEvent],
    store: NotificationStore,
    settings: Settings,
) -> None:
    for event in events:
        if store.has_notified(event.identifier):
            LOGGER.info("Skipping already-notified event %s", event.identifier)
            continue

        now_et = datetime.now(ET)
        message = build_alert_message(
            event,
            now_et.strftime("%Y-%m-%d %H:%M:%S %Z"),
            settings.alert_title,
        )
        if settings.dry_run:
            LOGGER.info("DRY_RUN would notify for %s:\n%s", event.identifier, message)
        else:
            send_telegram_message(
                bot_token=settings.telegram_bot_token or "",
                chat_id=settings.telegram_chat_id or "",
                text=message,
                timeout_seconds=settings.timeout_seconds,
            )
            LOGGER.info("Sent Telegram notification for %s", event.identifier)

        store.record_notification(
            source=event.source,
            identifier=event.identifier,
            title=event.title,
            notified_at=now_et,
            content=message,
        )


if __name__ == "__main__":
    sys.exit(main())

from datetime import datetime, timezone

from db import NotificationStore


def test_store_deduplicates_identifier(tmp_path):
    store = NotificationStore(str(tmp_path / "notifications.db"))

    assert not store.has_notified("abc")
    store.record_notification(
        source="SEC EDGAR",
        identifier="abc",
        title="SpaceX S-1",
        notified_at=datetime.now(timezone.utc),
        content="message",
    )

    assert store.has_notified("abc")
    assert store.count() == 1

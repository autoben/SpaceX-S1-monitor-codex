from notifiers.telegram import build_alert_message
from sources.sec_edgar import FilingEvent


def test_build_alert_message_escapes_markdown():
    message = build_alert_message(
        FilingEvent(
            source="SEC EDGAR",
            identifier="0000000000-26-000001",
            title="SpaceX S-1",
            form_type="S-1/A",
            url="https://www.sec.gov/test?a=1",
            excerpt="REGISTRATION_STATEMENT with chars . ! (test)",
            filed_at="2026-05-15",
            cik="0001234567",
            filer_name="Space Exploration Technologies Corp.",
        ),
        "2026-05-15 09:35:00 EDT",
    )

    assert "SPACEX S\\-1 ALERT" in message
    assert "S\\-1/A" in message
    assert "REGISTRATION\\_STATEMENT" in message
    assert "https://www\\.sec\\.gov/test?a\\=1" in message

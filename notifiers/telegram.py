"""Telegram Bot API notification channel."""

from __future__ import annotations

import logging

import requests

from sources.sec_edgar import FilingEvent


LOGGER = logging.getLogger(__name__)

MARKDOWN_V2_SPECIALS = r"_*[]()~`>#+-=|{}.!"


def send_telegram_message(
    *,
    bot_token: str,
    chat_id: str,
    text: str,
    timeout_seconds: float,
) -> None:
    response = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": False,
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()


def build_alert_message(
    event: FilingEvent,
    timestamp_et: str,
    alert_title: str = "SPACEX S-1 ALERT",
) -> str:
    lines = [
        f"*🚨 {_escape(alert_title)} 🚨*",
        f"*Time:* {_escape(timestamp_et)}",
        f"*Source:* {_escape(event.source)}",
        f"*Filing Type:* {_escape(event.form_type)}",
        f"*Filer:* {_escape(event.filer_name or 'Unknown')}",
        f"*CIK:* {_escape(event.cik or 'Unknown')}",
        f"*Accession:* `{_escape(event.identifier)}`",
        f"*URL:* {_escape(event.url)}",
        "",
        "*Excerpt:*",
        _escape(event.excerpt or "No description provided.")[:1200],
        "",
        "*Action items:*",
        "1\\. 立即查看 SEC EDGAR 确认真实性",
        "2\\. 观察 RKLB 盘中反应",
        "3\\. 按计划启动第一批 Call 卖出",
    ]
    return "\n".join(lines)


def _escape(value: str) -> str:
    return "".join(f"\\{char}" if char in MARKDOWN_V2_SPECIALS else char for char in value)

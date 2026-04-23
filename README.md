# SpaceX S-1 Monitor

V1 monitors the SEC EDGAR Full-Text Search API for public SpaceX registration filings and sends a Telegram alert once per unique accession number. It does not monitor confidential filings, because confidential submissions are not visible through public EDGAR.

## What V1 Watches

- Search terms: `Space Exploration Technologies`, `Space Exploration Technologies Corp`, `SpaceX`
- Form types: `S-1`, `S-1/A`, `DRS`, `DRS/A`
- Deduplication: permanent SQLite dedupe by SEC accession number
- Notification channel: Telegram Bot API

GitHub Actions is a convenient free scheduler, but scheduled jobs can be delayed or dropped under platform load. Use a VPS cron or Cloudflare Worker later if you need a stricter 5-minute SLA.

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Set a SEC User-Agent that identifies your monitor:

```bash
export SEC_USER_AGENT="SpaceX-S1-Monitor your_email@example.com"
```

## Telegram Setup

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`, choose a name and username, then copy the bot token.
3. Send any message to your new bot.
4. Visit this URL after replacing the token:

```text
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

5. Copy the `chat.id` value from the JSON response.
6. Export both values locally or add them as GitHub Actions secrets:

```bash
export TELEGRAM_BOT_TOKEN="123456:abc..."
export TELEGRAM_CHAT_ID="123456789"
```

## Running Locally

Dry-run mode logs would-be notifications without sending Telegram messages:

```bash
DRY_RUN=true python monitor.py
```

Use a temporary broad query for end-to-end testing:

```bash
TEST_QUERY=Apple DRY_RUN=true python monitor.py
```

When `TEST_QUERY` is set, both the SEC search term and the validation filter use that value, and the message title changes to `SEC FILING TEST ALERT`. Use a temporary DB if you do not want test alerts recorded in the default dedupe database:

```bash
TEST_QUERY=Apple DB_PATH=/tmp/spacex-s1-monitor-test.db DRY_RUN=true python monitor.py
```

To send a real Telegram test message, remove `DRY_RUN=true` after confirming `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set:

```bash
TEST_QUERY=Apple python monitor.py
```

Run tests:

```bash
pytest
```

## Expected Demo Output

Representative dry-run logs look like:

```text
INFO sources.sec_edgar: SEC query term='Space Exploration Technologies' returned 54 hit(s)
INFO sources.sec_edgar: SEC query term='Space Exploration Technologies Corp' returned 54 hit(s)
WARNING sources.sec_edgar: SEC query failed for term 'SpaceX': ...
INFO __main__: Found 0 validated SpaceX filing event(s)
INFO __main__: Notification DB row count: 0
```

If a validated public filing is found, the Telegram message includes ET time, source, filing type, filer, CIK, accession number, SEC URL, excerpt, and the RKLB action checklist from the requirements.

## GitHub Actions Deployment

1. Push this directory to a GitHub repository.
2. In GitHub, go to `Settings -> Secrets and variables -> Actions`.
3. Add repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `SEC_USER_AGENT`

4. Enable Actions if prompted.
5. Open the `SpaceX S-1 Monitor` workflow and run it manually once with `workflow_dispatch`.

The workflow commits `notifications.db` back to the repository so future scheduled runs do not resend the same accession number.

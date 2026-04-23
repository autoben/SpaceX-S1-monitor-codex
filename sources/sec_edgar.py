"""SEC EDGAR Full-Text Search source."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlencode

import requests


LOGGER = logging.getLogger(__name__)

SEC_SEARCH_URL = "https://efts.sec.gov/LATEST/search-index"
SPACE_X_PATTERNS = (
    "spacex",
    "space exploration technologies",
)


@dataclass(frozen=True)
class FilingEvent:
    source: str
    identifier: str
    title: str
    form_type: str
    url: str
    excerpt: str
    filed_at: str | None
    cik: str | None
    filer_name: str | None


def search_sec_edgar(
    *,
    search_terms: Iterable[str],
    form_types: Iterable[str],
    user_agent: str,
    timeout_seconds: float,
    max_results_per_query: int,
    validation_terms: Iterable[str] = SPACE_X_PATTERNS,
) -> list[FilingEvent]:
    events_by_identifier: dict[str, FilingEvent] = {}
    session = requests.Session()
    headers = {
        "User-Agent": user_agent,
        "Accept-Encoding": "gzip, deflate",
        "Host": "efts.sec.gov",
    }

    for term in search_terms:
        try:
            hits = _fetch_hits(
                session=session,
                term=term,
                form_types=form_types,
                headers=headers,
                timeout_seconds=timeout_seconds,
                max_results=max_results_per_query,
            )
        except requests.RequestException as exc:
            LOGGER.warning("SEC query failed for term %r: %s", term, exc)
            continue
        except ValueError as exc:
            LOGGER.warning("SEC query returned invalid data for term %r: %s", term, exc)
            continue

        for hit in hits:
            event = parse_filing_hit(hit)
            if event is None:
                continue
            if is_target_filing(event, validation_terms):
                events_by_identifier[event.identifier] = event

    return sorted(
        events_by_identifier.values(),
        key=lambda event: event.filed_at or "",
        reverse=True,
    )


def _fetch_hits(
    *,
    session: requests.Session,
    term: str,
    form_types: Iterable[str],
    headers: dict[str, str],
    timeout_seconds: float,
    max_results: int,
) -> list[dict[str, Any]]:
    params = {
        "q": f'"{term}"',
        "forms": ",".join(form_types),
        "start": "0",
        "count": str(max_results),
    }
    response = session.get(
        SEC_SEARCH_URL,
        params=params,
        headers=headers,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()

    hits = payload.get("hits", {}).get("hits")
    if not isinstance(hits, list):
        raise ValueError("missing hits.hits list in SEC response")
    LOGGER.info(
        "SEC query term=%r returned %s hit(s)",
        term,
        payload.get("hits", {}).get("total", {}).get("value", len(hits)),
    )
    return hits


def parse_filing_hit(hit: dict[str, Any]) -> FilingEvent | None:
    source = hit.get("_source")
    if not isinstance(source, dict):
        return None

    accession = _as_text(source.get("adsh")) or _accession_from_hit_id(hit.get("_id"))
    if not accession:
        return None

    ciks = _as_text_list(source.get("ciks"))
    cik = ciks[0] if ciks else None
    display_names = _as_text_list(source.get("display_names"))
    filer_name = display_names[0] if display_names else None
    form_type = _as_text(source.get("form")) or _as_text(source.get("file_type")) or "Unknown"
    description = _as_text(source.get("file_description")) or form_type
    filed_at = _as_text(source.get("file_date"))
    title = f"{filer_name or 'Unknown filer'} {form_type}".strip()
    excerpt_parts = [
        description,
        filer_name or "",
        f"Filed: {filed_at}" if filed_at else "",
    ]
    excerpt = " | ".join(part for part in excerpt_parts if part)

    return FilingEvent(
        source="SEC EDGAR",
        identifier=accession,
        title=title,
        form_type=form_type,
        url=build_filing_url(cik, accession, hit.get("_id")),
        excerpt=excerpt[:300],
        filed_at=filed_at,
        cik=cik,
        filer_name=filer_name,
    )


def is_spacex_filing(event: FilingEvent) -> bool:
    return is_target_filing(event, SPACE_X_PATTERNS)


def is_target_filing(event: FilingEvent, validation_terms: Iterable[str]) -> bool:
    haystack = " ".join(
        part
        for part in (
            event.filer_name,
            event.title,
            event.excerpt,
            event.identifier,
        )
        if part
    ).lower()
    patterns = [term.strip().lower() for term in validation_terms if term.strip()]
    return any(pattern in haystack for pattern in patterns)


def build_filing_url(cik: str | None, accession: str, hit_id: object | None = None) -> str:
    if cik:
        cik_without_zeros = str(int(cik))
        accession_no_dashes = accession.replace("-", "")
        return (
            "https://www.sec.gov/Archives/edgar/data/"
            f"{cik_without_zeros}/{accession_no_dashes}/{accession}-index.html"
        )

    if hit_id:
        return f"{SEC_SEARCH_URL}?{urlencode({'q': str(hit_id)})}"

    return f"{SEC_SEARCH_URL}?{urlencode({'q': accession})}"


def _accession_from_hit_id(value: object) -> str | None:
    text = _as_text(value)
    if not text:
        return None
    match = re.search(r"\d{10}-\d{2}-\d{6}", text)
    return match.group(0) if match else None


def _as_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _as_text_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _as_text(value)
    return [text] if text else []

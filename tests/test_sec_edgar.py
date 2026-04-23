from sources.sec_edgar import build_filing_url, is_spacex_filing, parse_filing_hit


def test_parse_sec_hit_into_event():
    event = parse_filing_hit(
        {
            "_id": "0000000000-26-000001:forms-1.htm",
            "_source": {
                "ciks": ["0001234567"],
                "display_names": [
                    "Space Exploration Technologies Corp.  (CIK 0001234567)"
                ],
                "form": "S-1",
                "file_description": "REGISTRATION STATEMENT",
                "file_date": "2026-05-15",
                "adsh": "0000000000-26-000001",
            },
        }
    )

    assert event is not None
    assert event.identifier == "0000000000-26-000001"
    assert event.form_type == "S-1"
    assert event.cik == "0001234567"
    assert "Archives/edgar/data/1234567" in event.url


def test_spacex_filter_accepts_real_filer_name():
    event = parse_filing_hit(
        {
            "_source": {
                "ciks": ["0001234567"],
                "display_names": ["SpaceX Corp.  (CIK 0001234567)"],
                "form": "DRS",
                "file_description": "Draft registration statement",
                "file_date": "2026-05-15",
                "adsh": "0000000000-26-000002",
            }
        }
    )

    assert event is not None
    assert is_spacex_filing(event)


def test_spacex_filter_rejects_unrelated_mention():
    event = parse_filing_hit(
        {
            "_source": {
                "ciks": ["0001825079"],
                "display_names": ["Velo3D, Inc.  (CIK 0001825079)"],
                "form": "S-1/A",
                "file_description": "S-1/A",
                "file_date": "2025-08-13",
                "adsh": "0001641172-25-023592",
            }
        }
    )

    assert event is not None
    assert not is_spacex_filing(event)


def test_build_sec_archive_url():
    assert (
        build_filing_url("0001234567", "0000000000-26-000001")
        == "https://www.sec.gov/Archives/edgar/data/1234567/000000000026000001/0000000000-26-000001-index.html"
    )

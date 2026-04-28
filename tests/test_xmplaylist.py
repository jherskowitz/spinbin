from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from scrapers.xmplaylist import fetch_plays


def _ts(minutes_ago):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )


def _resp(data):
    r = MagicMock()
    r.json.return_value = data
    r.raise_for_status = MagicMock()
    return r


@patch("scrapers.xmplaylist.requests.get")
def test_fetch_plays_parses_results(mock_get):
    mock_get.return_value = _resp({
        "next": None,
        "results": [
            {
                "id": "1",
                "timestamp": _ts(10),
                "track": {"title": "SEEIN' STARS", "artists": ["Turnstile"]},
                "spotify": {"albumImageMedium": "https://ex.com/m.jpg"},
            },
            {
                "id": "2",
                "timestamp": _ts(20),
                "track": {"title": "Collab", "artists": ["Artist A", "Artist B"]},
                "spotify": {},
            },
        ],
    })
    tracks = fetch_plays("siriusxmu")
    assert len(tracks) == 2
    assert tracks[0]["title"] == "SEEIN' STARS"
    assert tracks[0]["creator"] == "Turnstile"
    assert tracks[0]["image"] == "https://ex.com/m.jpg"
    assert tracks[1]["creator"] == "Artist A, Artist B"


@patch("scrapers.xmplaylist.requests.get")
def test_fetch_plays_filters_time_window(mock_get):
    mock_get.return_value = _resp({
        "next": None,
        "results": [
            {"id": "r", "timestamp": _ts(10), "track": {"title": "Recent", "artists": ["A"]}},
            {"id": "o", "timestamp": _ts(60 * 48), "track": {"title": "Old", "artists": ["B"]}},
        ],
    })
    tracks = fetch_plays("siriusxmu", hours=24)
    assert len(tracks) == 1
    assert tracks[0]["title"] == "Recent"


@patch("scrapers.xmplaylist.requests.get")
def test_fetch_plays_follows_pagination(mock_get):
    page1 = {
        "next": "https://xmplaylist.com/api/station/siriusxmu?last=1",
        "results": [
            {"id": "p1", "timestamp": _ts(5), "track": {"title": "P1", "artists": ["A"]}},
        ],
    }
    page2 = {
        "next": None,
        "results": [
            {"id": "p2", "timestamp": _ts(15), "track": {"title": "P2", "artists": ["B"]}},
        ],
    }
    responses = [_resp(page1), _resp(page2)]
    mock_get.side_effect = lambda *a, **kw: responses.pop(0)

    tracks = fetch_plays("siriusxmu")
    assert len(tracks) == 2
    assert [t["title"] for t in tracks] == ["P1", "P2"]


@patch("scrapers.xmplaylist.requests.get")
def test_fetch_plays_skips_incomplete_entries(mock_get):
    mock_get.return_value = _resp({
        "next": None,
        "results": [
            {"id": "1", "timestamp": _ts(5), "track": {"title": "", "artists": ["A"]}},
            {"id": "2", "timestamp": _ts(5), "track": {"title": "X", "artists": []}},
            {"id": "3", "timestamp": _ts(5), "track": {"title": "Good", "artists": ["A"]}},
        ],
    })
    tracks = fetch_plays("siriusxmu")
    assert len(tracks) == 1
    assert tracks[0]["title"] == "Good"

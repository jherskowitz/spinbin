import time
from unittest.mock import patch, MagicMock
from scrapers.onlineradiobox import fetch_plays, _split_artist_title


def _mock(data):
    r = MagicMock()
    r.json.return_value = data
    r.raise_for_status = MagicMock()
    return r


def test_split_artist_title():
    assert _split_artist_title("The Rolling Stones - Hot Stuff") == ("The Rolling Stones", "Hot Stuff")
    # Only first " - " separator (spaces matter)
    assert _split_artist_title("Crooked Fingers - (I'm Your) Bodhisattva - Remix") == (
        "Crooked Fingers", "(I'm Your) Bodhisattva - Remix",
    )
    # No separator → empty artist
    assert _split_artist_title("Unknown") == ("", "Unknown")
    # Hyphens without spaces don't split (e.g., band names like "Crosby-Stills")
    assert _split_artist_title("Crosby-Stills-Nash") == ("", "Crosby-Stills-Nash")


@patch("scrapers.onlineradiobox.requests.get")
def test_fetch_plays_parses_playlist(mock_get):
    now = int(time.time())
    mock_get.side_effect = lambda *a, **kw: _mock({
        "playlist": [
            {"id": "1", "name": "The Rolling Stones - Hot Stuff", "created": now - 60},
            {"id": "2", "name": "Rosali - Other Side", "created": now - 120},
        ],
    })
    tracks = fetch_plays("us", "bagel", days_back=1)
    assert len(tracks) == 2
    assert tracks[0]["creator"] == "The Rolling Stones"
    assert tracks[0]["title"] == "Hot Stuff"
    assert tracks[1]["creator"] == "Rosali"


@patch("scrapers.onlineradiobox.requests.get")
def test_fetch_plays_filters_time_window(mock_get):
    now = int(time.time())
    mock_get.side_effect = lambda *a, **kw: _mock({
        "playlist": [
            {"id": "r", "name": "A - Recent", "created": now - 60},
            {"id": "o", "name": "B - Old", "created": now - 60 * 60 * 48},
        ],
    })
    tracks = fetch_plays("us", "bagel", hours=24, days_back=1)
    assert len(tracks) == 1
    assert tracks[0]["title"] == "Recent"


@patch("scrapers.onlineradiobox.requests.get")
def test_fetch_plays_dedupes_across_days(mock_get):
    """Fetching day=0 + day=1 can return overlapping entries; dedupe by id."""
    now = int(time.time())
    calls = {"n": 0}

    def side_effect(*a, **kw):
        calls["n"] += 1
        # Both days return the same entry
        return _mock({
            "playlist": [
                {"id": "same", "name": "Dup - Track", "created": now - 60},
                {"id": str(calls["n"]), "name": f"Day{calls['n']} - X", "created": now - 60},
            ],
        })

    mock_get.side_effect = side_effect
    tracks = fetch_plays("us", "bagel", days_back=2)
    # "same" counted once; two unique per-day entries added
    titles = [t["title"] for t in tracks]
    assert titles.count("Track") == 1
    assert "X" in titles


@patch("scrapers.onlineradiobox.requests.get")
def test_fetch_plays_falls_back_to_slug_when_no_artist(mock_get):
    now = int(time.time())
    mock_get.side_effect = lambda *a, **kw: _mock({
        "playlist": [{"id": "1", "name": "NoSeparator", "created": now}],
    })
    tracks = fetch_plays("us", "bagel", days_back=1)
    assert len(tracks) == 1
    assert tracks[0]["creator"] == "bagel"
    assert tracks[0]["title"] == "NoSeparator"

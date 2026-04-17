import time
from unittest.mock import patch, MagicMock
from scrapers.somafm import fetch_plays


def _now_ts():
    return int(time.time())


def _mock_resp(data):
    r = MagicMock()
    r.json.return_value = data
    r.raise_for_status = MagicMock()
    return r


@patch("scrapers.somafm.requests.get")
def test_fetch_plays_filters_by_time_window(mock_get):
    now = _now_ts()
    mock_get.return_value = _mock_resp({
        "id": "groovesalad",
        "songs": [
            {"title": "Recent Track", "artist": "A", "album": "Alb", "albumArt": "", "date": str(now - 60)},
            {"title": "Old Track", "artist": "B", "album": "", "albumArt": "", "date": str(now - 60 * 60 * 48)},
        ],
    })

    tracks = fetch_plays(hours=24)
    assert len(tracks) == 1
    assert tracks[0]["title"] == "Recent Track"
    assert tracks[0]["creator"] == "A"
    assert tracks[0]["album"] == "Alb"


@patch("scrapers.somafm.requests.get")
def test_fetch_plays_skips_empty_entries(mock_get):
    now = _now_ts()
    mock_get.return_value = _mock_resp({
        "songs": [
            {"title": "", "artist": "No Title", "date": str(now)},
            {"title": "No Artist", "artist": "", "date": str(now)},
            {"title": "Good", "artist": "Artist", "date": str(now)},
        ],
    })
    tracks = fetch_plays()
    assert len(tracks) == 1
    assert tracks[0]["title"] == "Good"

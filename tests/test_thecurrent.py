from unittest.mock import patch, MagicMock
from scrapers.thecurrent import fetch_plays


def _mock_resp(data):
    r = MagicMock()
    r.json.return_value = data
    r.raise_for_status = MagicMock()
    return r


@patch("scrapers.thecurrent.requests.get")
def test_fetch_plays_with_songs(mock_get):
    mock_get.return_value = _mock_resp({
        "songs": [
            {"title": "Song One", "artist": "Artist A", "album": "Album A", "albumArt": "https://ex.com/a.jpg"},
            {"title": "Song Two", "artist": "Artist B"},
        ],
    })
    tracks = fetch_plays()
    assert len(tracks) == 2
    assert tracks[0]["title"] == "Song One"
    assert tracks[0]["image"] == "https://ex.com/a.jpg"
    assert tracks[1]["album"] == ""


@patch("scrapers.thecurrent.requests.get")
def test_fetch_plays_empty_response(mock_get):
    mock_get.return_value = _mock_resp({"songs": []})
    assert fetch_plays() == []


@patch("scrapers.thecurrent.requests.get")
def test_fetch_plays_skips_incomplete(mock_get):
    mock_get.return_value = _mock_resp({
        "songs": [
            {"title": "", "artist": "No Title"},
            {"title": "No Artist", "artist": ""},
            {"title": "Good", "artist": "Real"},
        ],
    })
    tracks = fetch_plays()
    assert len(tracks) == 1
    assert tracks[0]["title"] == "Good"

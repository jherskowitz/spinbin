from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from scrapers.kexp import fetch_plays


def _airdate(minutes_ago):
    """Return an ISO-8601 airdate that is `minutes_ago` minutes before now.

    KEXP's scraper filters out any play whose airdate is older than the
    24-hour cutoff, so hard-coded dates eventually fall outside the window
    and tests go red on a calendar flip. Generate dates relative to now.
    """
    dt = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")


@patch("scrapers.kexp.requests.get")
def test_fetch_plays_filters_airbreaks(mock_get):
    response = {
        "next": None,
        "previous": None,
        "results": [
            {
                "play_type": "trackplay",
                "airdate": _airdate(10),
                "song": "Stayin' Alive",
                "artist": "Tropical Fuck Storm",
                "album": "A Laughing Death in Meatspace",
                "image_uri": "https://example.com/art.jpg",
                "comment": "",
            },
            {
                "play_type": "airbreak",
                "airdate": _airdate(15),
                "song": None,
                "artist": None,
                "album": None,
                "image_uri": None,
                "comment": "",
            },
            {
                "play_type": "trackplay",
                "airdate": _airdate(20),
                "song": "Boredom",
                "artist": "Buzzcocks",
                "album": "Singles Going Steady",
                "image_uri": None,
                "comment": "",
            },
        ],
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = response
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    tracks = fetch_plays()
    assert len(tracks) == 2
    assert tracks[0]["title"] == "Stayin' Alive"
    assert tracks[0]["creator"] == "Tropical Fuck Storm"
    assert tracks[0]["album"] == "A Laughing Death in Meatspace"
    assert tracks[1]["title"] == "Boredom"
    assert tracks[1]["creator"] == "Buzzcocks"


@patch("scrapers.kexp.requests.get")
def test_fetch_plays_handles_pagination(mock_get):
    page1 = {
        "next": "https://api.kexp.org/v2/plays/?offset=2",
        "results": [
            {
                "play_type": "trackplay",
                "airdate": _airdate(10),
                "song": "Song A",
                "artist": "Artist A",
                "album": "Album A",
                "image_uri": None,
                "comment": "",
            },
        ],
    }
    page2 = {
        "next": None,
        "results": [
            {
                "play_type": "trackplay",
                "airdate": _airdate(30),
                "song": "Song B",
                "artist": "Artist B",
                "album": "Album B",
                "image_uri": None,
                "comment": "",
            },
        ],
    }
    resp1 = MagicMock()
    resp1.json.return_value = page1
    resp1.raise_for_status = MagicMock()
    resp2 = MagicMock()
    resp2.json.return_value = page2
    resp2.raise_for_status = MagicMock()
    mock_get.side_effect = [resp1, resp2]

    tracks = fetch_plays()
    assert len(tracks) == 2
    assert tracks[0]["title"] == "Song A"
    assert tracks[1]["title"] == "Song B"

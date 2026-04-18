import time
from unittest.mock import patch, MagicMock
from scrapers.radioparadise import fetch_plays


def _mock(data):
    r = MagicMock()
    r.json.return_value = data
    r.raise_for_status = MagicMock()
    return r


@patch("scrapers.radioparadise.requests.get")
def test_fetch_plays_parses_song_object(mock_get):
    now = int(time.time())
    mock_get.return_value = _mock({
        "song": {
            "0": {
                "artist": "Buena Vista Social Club",
                "title": "Chan Chan",
                "album": "Buena Vista Social Club",
                "sched_time": str(now - 60),
                "cover": "covers/l/10842.jpg",
            },
            "1": {
                "artist": "Kings of Leon",
                "title": "The End",
                "album": "Come Around Sundown",
                "sched_time": str(now - 300),
                "cover": "",
            },
        },
    })
    tracks = fetch_plays(channel=0)
    assert len(tracks) == 2
    assert tracks[0]["creator"] == "Buena Vista Social Club"
    assert tracks[0]["title"] == "Chan Chan"
    assert tracks[0]["image"].startswith("https://img.radioparadise.com/covers/l/")


@patch("scrapers.radioparadise.requests.get")
def test_fetch_plays_filters_time_window(mock_get):
    now = int(time.time())
    mock_get.return_value = _mock({
        "song": {
            "0": {"artist": "A", "title": "Recent", "sched_time": str(now - 60)},
            "1": {"artist": "B", "title": "Old", "sched_time": str(now - 60 * 60 * 48)},
        },
    })
    tracks = fetch_plays(channel=0, hours=24)
    assert len(tracks) == 1
    assert tracks[0]["title"] == "Recent"


@patch("scrapers.radioparadise.requests.get")
def test_fetch_plays_skips_incomplete(mock_get):
    now = int(time.time())
    mock_get.return_value = _mock({
        "song": {
            "0": {"artist": "", "title": "No Artist", "sched_time": str(now)},
            "1": {"artist": "Real", "title": "Good", "sched_time": str(now)},
        },
    })
    tracks = fetch_plays()
    assert len(tracks) == 1
    assert tracks[0]["creator"] == "Real"

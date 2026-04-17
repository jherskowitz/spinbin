import time
from unittest.mock import patch, MagicMock
from scrapers.vintageobscura import fetch_plays, _split_artist_title


def _mock(data):
    r = MagicMock()
    r.json.return_value = data
    r.raise_for_status = MagicMock()
    return r


def test_split_artist_title_basic():
    artist, title = _split_artist_title("Leslie And Monique - Times Without Love (Netherlands, synthpop) (1982)")
    assert artist == "Leslie And Monique"
    assert title == "Times Without Love (Netherlands, synthpop) (1982)"


def test_split_artist_title_only_splits_on_first_dash():
    artist, title = _split_artist_title("Artist - Song - Subtitle")
    assert artist == "Artist"
    assert title == "Song - Subtitle"


def test_split_artist_title_no_separator():
    artist, title = _split_artist_title("Just A Song Name")
    assert artist == ""
    assert title == "Just A Song Name"


@patch("scrapers.vintageobscura.requests.get")
def test_fetch_plays_parses_feed(mock_get):
    now = int(time.time())
    mock_get.return_value = _mock([
        {
            "title": "Cletus Black - You As You [USA, Psyche] (1981)",
            "start_timestamp": now - 60,
            "img": "https://example.com/1.jpg",
            "show": "Psychedelia",
        },
        {
            "title": "Reme Izabo - (Ayamayama) The Same Man [Nigeria, Psych] (1972)",
            "start_timestamp": now - 120,
            "img": "https://example.com/2.jpg",
            "show": "Psychedelia",
        },
    ])
    tracks = fetch_plays()
    assert len(tracks) == 2
    assert tracks[0]["creator"] == "Cletus Black"
    assert tracks[0]["title"] == "You As You [USA, Psyche] (1981)"
    assert tracks[0]["album"] == "Psychedelia"
    assert tracks[0]["image"] == "https://example.com/1.jpg"


@patch("scrapers.vintageobscura.requests.get")
def test_fetch_plays_filters_by_time_window(mock_get):
    now = int(time.time())
    mock_get.return_value = _mock([
        {"title": "New - Song", "start_timestamp": now - 60, "img": "", "show": ""},
        {"title": "Old - Song", "start_timestamp": now - 60 * 60 * 48, "img": "", "show": ""},
    ])
    tracks = fetch_plays(hours=24)
    assert len(tracks) == 1
    assert tracks[0]["title"] == "Song"
    assert tracks[0]["creator"] == "New"


@patch("scrapers.vintageobscura.requests.get")
def test_fetch_plays_handles_missing_artist(mock_get):
    now = int(time.time())
    mock_get.return_value = _mock([
        {"title": "Standalone Track Title", "start_timestamp": now, "show": "World Music"},
    ])
    tracks = fetch_plays()
    assert len(tracks) == 1
    assert tracks[0]["creator"] == "World Music"  # falls back to show
    assert tracks[0]["title"] == "Standalone Track Title"

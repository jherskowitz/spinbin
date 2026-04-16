from unittest.mock import patch, MagicMock
from scrapers.kcrw import fetch_plays


MOCK_PLAYS = [
    {
        "title": "Half the Man",
        "artist": "Jamiroquai",
        "album": "The Return of the Space Cowboy",
        "albumImage": None,
        "albumImageLarge": None,
        "datetime": "2026-04-16T10:17:22-07:00",
    },
    {
        "title": None,
        "artist": "[BREAK]",
        "album": None,
        "albumImage": None,
        "albumImageLarge": None,
        "datetime": "2026-04-16T10:01:09-07:00",
    },
    {
        "title": "Enough",
        "artist": "Jeff Tweedy",
        "album": "Twilight Override",
        "albumImage": "https://example.com/small.jpg",
        "albumImageLarge": "https://example.com/large.jpg",
        "datetime": "2026-04-16T09:21:30-07:00",
    },
]


def _make_mock_resp(data):
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status = MagicMock()
    return resp


@patch("scrapers.kcrw.requests.get")
def test_fetch_plays_filters_breaks(mock_get):
    # One call returns plays, second call (if any) returns empty
    mock_get.side_effect = lambda *a, **kw: _make_mock_resp(
        MOCK_PLAYS if "04/16" in str(a) else []
    )

    tracks = fetch_plays(hours=1)
    assert len(tracks) == 2
    assert tracks[0]["title"] == "Half the Man"
    assert tracks[0]["creator"] == "Jamiroquai"
    assert tracks[1]["title"] == "Enough"
    assert tracks[1]["creator"] == "Jeff Tweedy"
    assert tracks[1]["image"] == "https://example.com/large.jpg"


@patch("scrapers.kcrw.requests.get")
def test_fetch_plays_prefers_large_artwork(mock_get):
    plays = [
        {
            "title": "Song",
            "artist": "Artist",
            "album": "Album",
            "albumImage": "https://example.com/small.jpg",
            "albumImageLarge": None,
            "datetime": "2026-04-16T10:00:00-07:00",
        },
    ]
    mock_get.side_effect = lambda *a, **kw: _make_mock_resp(
        plays if "04/16" in str(a) else []
    )

    tracks = fetch_plays(hours=1)
    assert len(tracks) == 1
    assert tracks[0]["image"] == "https://example.com/small.jpg"

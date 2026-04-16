from unittest.mock import patch, MagicMock
from scrapers.kexp import fetch_plays


MOCK_RESPONSE = {
    "next": None,
    "previous": None,
    "results": [
        {
            "play_type": "trackplay",
            "airdate": "2026-04-16T12:00:00-07:00",
            "song": "Stayin' Alive",
            "artist": "Tropical Fuck Storm",
            "album": "A Laughing Death in Meatspace",
            "image_uri": "https://example.com/art.jpg",
            "comment": "",
        },
        {
            "play_type": "airbreak",
            "airdate": "2026-04-16T11:55:00-07:00",
            "song": None,
            "artist": None,
            "album": None,
            "image_uri": None,
            "comment": "",
        },
        {
            "play_type": "trackplay",
            "airdate": "2026-04-16T11:50:00-07:00",
            "song": "Boredom",
            "artist": "Buzzcocks",
            "album": "Singles Going Steady",
            "image_uri": None,
            "comment": "",
        },
    ],
}


@patch("scrapers.kexp.requests.get")
def test_fetch_plays_filters_airbreaks(mock_get):
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_RESPONSE
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
                "airdate": "2026-04-16T12:00:00-07:00",
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
                "airdate": "2026-04-16T11:00:00-07:00",
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

from unittest.mock import patch, MagicMock
from scrapers.nts import fetch_plays


def _resp(data):
    r = MagicMock()
    r.json.return_value = data
    r.raise_for_status = MagicMock()
    return r


LIVE_RESPONSE = {
    "results": [
        {
            "channel_name": "1",
            "now": {
                "broadcast_title": "Show One",
                "embeds": {
                    "details": {
                        "name": "Show One",
                        "media": {"picture_medium": "https://ex.com/s1.jpg"},
                        "links": [
                            {"rel": "self", "href": "https://nts/shows/s1"},
                            {"rel": "tracklist", "href": "https://nts/shows/s1/tracklist"},
                        ],
                    },
                },
            },
        },
        {
            "channel_name": "2",
            "now": {
                "broadcast_title": "Show Two",
                "embeds": {
                    "details": {
                        "name": "Show Two",
                        "media": {},
                        "links": [
                            {"rel": "tracklist", "href": "https://nts/shows/s2/tracklist"},
                        ],
                    },
                },
            },
        },
    ],
}

TL_1 = {"results": [
    {"artist": "Arvo Pärt", "title": "Fratres"},
    {"artist": "John Tavener", "title": "The Protecting Veil"},
]}

TL_2_EMPTY = {"results": []}


@patch("scrapers.nts.requests.get")
def test_fetch_plays_aggregates_tracklists_from_live_channels(mock_get):
    def side_effect(url, *args, **kwargs):
        if url.endswith("/live"):
            return _resp(LIVE_RESPONSE)
        if url.endswith("/s1/tracklist"):
            return _resp(TL_1)
        if url.endswith("/s2/tracklist"):
            return _resp(TL_2_EMPTY)
        return _resp({"results": []})

    mock_get.side_effect = side_effect
    tracks = fetch_plays()
    assert len(tracks) == 2
    assert tracks[0]["creator"] == "Arvo Pärt"
    assert tracks[0]["album"] == "Show One"
    assert tracks[0]["image"] == "https://ex.com/s1.jpg"
    assert tracks[1]["creator"] == "John Tavener"


@patch("scrapers.nts.requests.get")
def test_fetch_plays_handles_missing_tracklist_link(mock_get):
    def side_effect(url, *args, **kwargs):
        return _resp({"results": [{
            "channel_name": "1",
            "now": {"embeds": {"details": {"links": []}}},
        }]})
    mock_get.side_effect = side_effect
    assert fetch_plays() == []

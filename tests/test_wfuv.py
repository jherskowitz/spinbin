from unittest.mock import patch, MagicMock
from scrapers.wfuv import fetch_plays


RSS_SAMPLE = b"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>On Air Playlist</title>
    <link>https://wfuv.org/</link>
    <description/>
    <item>
      <title>I'll Be There</title>
      <link>https://wfuv.org/</link>
      <description>Nick Lowe</description>
      <pubDate>04/17, 8:58am</pubDate>
    </item>
    <item>
      <title>Peace Train</title>
      <description>Cat Stevens</description>
      <pubDate>04/17, 8:30am</pubDate>
    </item>
    <item>
      <title></title>
      <description>Missing Title</description>
    </item>
  </channel>
</rss>
"""


def _mock_resp(content):
    r = MagicMock()
    r.content = content
    r.raise_for_status = MagicMock()
    return r


@patch("scrapers.wfuv.requests.get")
def test_fetch_plays_parses_rss(mock_get):
    mock_get.return_value = _mock_resp(RSS_SAMPLE)
    tracks = fetch_plays()
    assert len(tracks) == 2
    assert tracks[0]["title"] == "I'll Be There"
    assert tracks[0]["creator"] == "Nick Lowe"
    assert tracks[1]["title"] == "Peace Train"
    assert tracks[1]["creator"] == "Cat Stevens"

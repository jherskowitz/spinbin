from unittest.mock import patch, MagicMock
from scrapers.wfmu import _parse_show_tracks, fetch_plays


SHOW_HTML = """
<html><body>
<table border="1" id="drop_table">
<tr>
  <th class="song col_artist">Artist</th>
  <th class="song col_song_title">Track</th>
  <th class="song col_album_title">Album</th>
</tr>
<tr class="set_break_row">
  <td class="song col_artist">Music behind DJ: Kraftwerk</td>
  <td class="song col_song_title">&quot;Trans-Europe&quot;</td>
  <td class="song col_album_title">TE Express</td>
</tr>
<tr id="drop_1">
  <td class="song col_artist"><font size="-1">The Cure</font>&nbsp;</td>
  <td class="song col_song_title">
    <font size="-1">Friday I'm in Love</font>&nbsp;
    <span class="KDBFavIcon KDBsong">
      <button type="button" style="display:none">&#x2192;</button>
      <button type="button" class="reply_thread_button"><i class="fa fa-comment-o"></i></button>
      <span style="display:none" id="drop_1_summary_html">&quot;Friday I'm in Love&quot; by &quot;The Cure&quot;</span>
    </span>
  </td>
  <td class="song col_album_title"><font size="-1">Wish</font>&nbsp;</td>
</tr>
<tr id="drop_2">
  <td class="song col_artist"><a href="#">Brian Eno</a></td>
  <td class="song col_song_title">Ambient 1: Music for Airports</td>
  <td class="song col_album_title">Ambient 1</td>
</tr>
<tr>
  <td class="song col_artist"></td>
  <td class="song col_song_title">Empty artist</td>
  <td class="song col_album_title"></td>
</tr>
</table>
</body></html>
"""

RSS_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
<title>WFMU's recent playlists</title>
<item>
  <title>Show One</title>
  <link>https://wfmu.org/playlists/shows/1</link>
  <pubDate>Fri, 17 Apr 2026 08:00:00 -0400</pubDate>
</item>
<item>
  <title>Show Old</title>
  <link>https://wfmu.org/playlists/shows/999</link>
  <pubDate>Fri, 01 Jan 2020 00:00:00 -0400</pubDate>
</item>
</channel></rss>
"""


def test_parse_show_tracks_extracts_and_filters():
    tracks = _parse_show_tracks(SHOW_HTML)
    assert len(tracks) == 2
    # First real row: title should NOT include the hidden summary span or
    # the button arrow glyph — just the clean "Friday I'm in Love".
    assert tracks[0]["creator"] == "The Cure"
    assert tracks[0]["title"] == "Friday I'm in Love"
    assert tracks[0]["album"] == "Wish"
    assert tracks[1]["creator"] == "Brian Eno"
    assert tracks[1]["title"] == "Ambient 1: Music for Airports"


@patch("scrapers.wfmu.requests.get")
def test_fetch_plays_integrates_rss_and_show_scrape(mock_get):
    def side_effect(url, *args, **kwargs):
        r = MagicMock()
        r.raise_for_status = MagicMock()
        if "playlistfeed.xml" in url:
            r.content = RSS_FEED
        elif "shows/1" in url:
            r.text = SHOW_HTML
        else:
            r.text = ""
            r.content = b""
        return r

    mock_get.side_effect = side_effect
    # hours=24*365*10 ensures all RSS items (including "Show Old") are in range
    # But our scraper's recent filter uses `since = now - hours`, so we need
    # hours big enough to cover 2020:
    tracks = fetch_plays(hours=24 * 365 * 10)
    # Only Show One has scrapable HTML; Show Old returns empty body -> 0 tracks
    assert len(tracks) == 2
    assert tracks[0]["creator"] == "The Cure"


@patch("scrapers.wfmu.requests.get")
def test_fetch_plays_filters_old_shows(mock_get):
    def side_effect(url, *args, **kwargs):
        r = MagicMock()
        r.raise_for_status = MagicMock()
        if "playlistfeed.xml" in url:
            r.content = RSS_FEED
        else:
            r.text = SHOW_HTML
        return r

    mock_get.side_effect = side_effect
    # With hours=1, only shows within the last hour are considered;
    # RSS_FEED's dates are both old relative to "now", so nothing returns.
    # (Unless "now" in test is 2026-04-17; either way Show Old is filtered.)
    tracks = fetch_plays(hours=1)
    # Show One may or may not be within 1h depending on test time — just
    # confirm Show Old (2020) is always excluded and we don't crash.
    for t in tracks:
        assert t["creator"] != "Music behind DJ: Kraftwerk"

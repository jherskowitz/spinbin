from unittest.mock import patch, MagicMock
from scrapers.xrayfm import _parse_rows, fetch_plays


SAMPLE = """
<html><body>
<table>
  <tr><th class="track-time">Time</th><th class="track-title">Title</th><th class="track-artist">Artist</th></tr>
  <tr class="track">
    <td class="track-time">11:04pm</td>
    <td class="track-art">&nbsp;</td>
    <td class="track-title">Guest Mix&nbsp;</td>
    <td class="track-artist">Saltfeend&nbsp;</td>
    <td class="track-album">Guest Mix&nbsp;</td>
    <td class="track-label">Beats, Bass &amp; Beyond</td>
  </tr>
  <tr class="track">
    <td class="track-time">10:55pm</td>
    <td class="track-title">Song Two</td>
    <td class="track-artist">Artist Two</td>
    <td class="track-album">Album Two</td>
  </tr>
  <tr class="track">
    <td class="track-title"></td>
    <td class="track-artist">Empty Title</td>
  </tr>
</table>
</body></html>
"""


def test_parse_rows_extracts_tracks():
    rows = _parse_rows(SAMPLE)
    assert len(rows) == 2
    assert rows[0]["title"] == "Guest Mix"
    assert rows[0]["creator"] == "Saltfeend"
    assert rows[0]["album"] == "Guest Mix"
    assert rows[1]["title"] == "Song Two"
    assert rows[1]["creator"] == "Artist Two"


@patch("scrapers.xrayfm.requests.get")
def test_fetch_plays_integrates_request(mock_get):
    r = MagicMock()
    r.text = SAMPLE
    r.raise_for_status = MagicMock()
    mock_get.return_value = r
    tracks = fetch_plays()
    assert len(tracks) == 2
    assert tracks[0]["creator"] == "Saltfeend"

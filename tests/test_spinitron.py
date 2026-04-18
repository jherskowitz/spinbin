from unittest.mock import patch, MagicMock
from scrapers.spinitron import fetch_plays


SAMPLE = '''
<html><body>
<div class="spins">
  <div class="spin-item" data-spin="{&quot;i&quot;:&quot;AAA&quot;,&quot;a&quot;:&quot;Black Sabbath&quot;,&quot;s&quot;:&quot;Sweet Leaf&quot;,&quot;r&quot;:&quot;Master of Reality&quot;}" data-key="1"></div>
  <div class="spin-item" data-spin="{&quot;i&quot;:&quot;BBB&quot;,&quot;a&quot;:&quot;Sleep&quot;,&quot;s&quot;:&quot;Marijuanaut&#039;s Theme&quot;,&quot;r&quot;:&quot;The Sciences&quot;}" data-key="2"></div>
  <!-- duplicate spin -->
  <div class="spin-item" data-spin="{&quot;i&quot;:&quot;AAA&quot;,&quot;a&quot;:&quot;Black Sabbath&quot;,&quot;s&quot;:&quot;Sweet Leaf&quot;,&quot;r&quot;:&quot;Master of Reality&quot;}" data-key="3"></div>
  <!-- invalid json -->
  <div class="spin-item" data-spin="not-json"></div>
  <!-- missing artist -->
  <div class="spin-item" data-spin="{&quot;a&quot;:&quot;&quot;,&quot;s&quot;:&quot;Orphan&quot;,&quot;r&quot;:&quot;X&quot;}"></div>
</div>
</body></html>
'''


def _mock_response(text):
    r = MagicMock()
    r.text = text
    r.raise_for_status = MagicMock()
    return r


@patch("scrapers.spinitron.requests.get")
def test_fetch_plays_parses_data_spin(mock_get):
    mock_get.return_value = _mock_response(SAMPLE)
    tracks = fetch_plays("WPRB")
    assert len(tracks) == 2
    assert tracks[0]["creator"] == "Black Sabbath"
    assert tracks[0]["title"] == "Sweet Leaf"
    assert tracks[0]["album"] == "Master of Reality"
    # HTML entity `&#039;` decoded to apostrophe
    assert tracks[1]["title"] == "Marijuanaut's Theme"


@patch("scrapers.spinitron.requests.get")
def test_fetch_plays_uses_station_slug_in_url(mock_get):
    mock_get.return_value = _mock_response(SAMPLE)
    fetch_plays("KALX")
    called_url = mock_get.call_args[0][0]
    assert "KALX" in called_url

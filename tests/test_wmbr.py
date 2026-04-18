from unittest.mock import patch, MagicMock
from scrapers.wmbr import fetch_plays


# Real WMBR dynamic.xml shape: a <wmbr_plays> whose *contents* are
# HTML-entity-encoded HTML.
SAMPLE = """<?xml version="1.0" encoding="utf-8" ?>
<wmbr_dynamic version="1.0">
  <wmbr_info>Now playing Artist</wmbr_info>
  <wmbr_plays>&lt;p class=&quot;recent&quot;&gt;7:45p&amp;nbsp;&lt;b&gt;Working For a Nuclear Free City&lt;/b&gt;: Eighty Eight&lt;/p&gt;
&lt;p class=&quot;recent&quot;&gt;7:40p&amp;nbsp;&lt;b&gt;Godzillionaire&lt;/b&gt;: Drowning All Night&lt;/p&gt;
&lt;p class=&quot;recent&quot;&gt;7:36p&amp;nbsp;&lt;b&gt;Pez Globo&lt;/b&gt;: Paroxismo&lt;/p&gt;
&lt;p class=&quot;recent&quot;&gt;7:28p&amp;nbsp;&lt;b&gt;&lt;a href=&quot;http://x&quot;&gt;Laid Back&lt;/a&gt;&lt;/b&gt;: White Horse&lt;/p&gt;</wmbr_plays>
</wmbr_dynamic>
"""


def _mock(text):
    r = MagicMock()
    r.text = text
    r.raise_for_status = MagicMock()
    return r


@patch("scrapers.wmbr.requests.get")
def test_fetch_plays_parses_dynamic_xml(mock_get):
    mock_get.return_value = _mock(SAMPLE)
    tracks = fetch_plays()
    assert len(tracks) == 4
    assert tracks[0]["creator"] == "Working For a Nuclear Free City"
    assert tracks[0]["title"] == "Eighty Eight"
    assert tracks[1]["creator"] == "Godzillionaire"
    # Nested <a> tags inside <b> should be stripped to plain text
    assert tracks[3]["creator"] == "Laid Back"
    assert tracks[3]["title"] == "White Horse"


@patch("scrapers.wmbr.requests.get")
def test_fetch_plays_handles_empty_feed(mock_get):
    mock_get.return_value = _mock("<wmbr_dynamic><wmbr_plays></wmbr_plays></wmbr_dynamic>")
    assert fetch_plays() == []

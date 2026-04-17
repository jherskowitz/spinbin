import os
import tempfile
from unittest.mock import patch
from generate import generate_playlist


MOCK_TRACKS = [
    {"title": "Song A", "creator": "Artist A", "album": "Album A", "image": ""},
    {"title": "Song B", "creator": "Artist B", "album": "Album B", "image": ""},
]


@patch("generate.kexp.fetch_plays")
def test_generate_creates_xspf_file(mock_fetch):
    mock_fetch.return_value = MOCK_TRACKS
    with tempfile.TemporaryDirectory() as tmpdir:
        generate_playlist("kexp", tmpdir)
        outfile = os.path.join(tmpdir, "kexp-today.xspf")
        assert os.path.exists(outfile)
        content = open(outfile, "rb").read()
        assert b"Song A" in content
        assert b"Artist A" in content
        assert b"Song B" in content


@patch("generate.kexp.fetch_plays")
def test_generate_skips_empty_playlist(mock_fetch):
    mock_fetch.return_value = []
    with tempfile.TemporaryDirectory() as tmpdir:
        generate_playlist("kexp", tmpdir)
        outfile = os.path.join(tmpdir, "kexp-today.xspf")
        assert not os.path.exists(outfile)


@patch("generate.kexp.fetch_plays")
def test_generate_unescapes_html_entities_in_metadata(mock_fetch):
    """Sources sometimes pre-encode '&' as '&amp;'. Verify we decode before
    writing, so Parachord sees 'Earth Wind & Fire', not 'Earth Wind &amp; Fire'."""
    mock_fetch.return_value = [
        {"title": "Song &amp; Dance", "creator": "Earth Wind &amp; Fire", "album": "It&#39;s Great", "image": ""},
        # Double-encoded
        {"title": "Tricky", "creator": "Me &amp;amp; You", "album": "", "image": ""},
        {"title": "Quotes", "creator": "Sly &amp; the Family Stone", "album": "&quot;Fresh&quot;", "image": ""},
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        generate_playlist("kexp", tmpdir)
        outfile = os.path.join(tmpdir, "kexp-today.xspf")
        assert os.path.exists(outfile)
        content = open(outfile, "rb").read()

        # After XML serialization, '&' gets escaped to '&amp;' but '&amp;'
        # entity should NOT appear doubled (which would be '&amp;amp;').
        assert b"&amp;amp;" not in content, "Double-encoding detected in XSPF output"

        # The raw escape sequence '&amp;' should appear exactly (one level of
        # XML escaping of a literal '&'), and there should be no literal
        # '&amp;' substring preserved from the source (those should now be '&').
        # Easiest check: parse the XML back and verify final string values.
        import xml.etree.ElementTree as ET
        ns = {"x": "http://xspf.org/ns/0/"}
        root = ET.fromstring(content)
        tracks = root.findall(".//x:track", ns)
        assert len(tracks) == 3

        creators = [t.findtext("x:creator", default="", namespaces=ns) for t in tracks]
        titles = [t.findtext("x:title", default="", namespaces=ns) for t in tracks]
        albums = [t.findtext("x:album", default="", namespaces=ns) for t in tracks]

        assert creators[0] == "Earth Wind & Fire"
        assert titles[0] == "Song & Dance"
        assert albums[0] == "It's Great"
        # Double-encoded source should also end up with just one '&'
        assert creators[1] == "Me & You"
        # Quotes
        assert creators[2] == "Sly & the Family Stone"
        assert albums[2] == '"Fresh"'

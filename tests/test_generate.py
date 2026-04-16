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

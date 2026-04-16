from xspf import Xspf


def test_empty_playlist_generates_valid_xml():
    x = Xspf()
    x.title = "Test Playlist"
    xml_bytes = x.toXml()
    assert b"Test Playlist" in xml_bytes


def test_playlist_with_tracks():
    x = Xspf()
    x.title = "My Playlist"
    x.add_track(title="Song One", creator="Artist A", album="Album X")
    x.add_track(title="Song Two", creator="Artist B")
    xml_bytes = x.toXml()
    assert b"Song One" in xml_bytes
    assert b"Artist A" in xml_bytes
    assert b"Album X" in xml_bytes
    assert b"Song Two" in xml_bytes
    assert b"Artist B" in xml_bytes


def test_track_with_all_fields():
    x = Xspf()
    x.add_track(
        title="Test Song",
        creator="Test Artist",
        album="Test Album",
        image="https://example.com/art.jpg",
        location="https://example.com/song.mp3",
    )
    xml_bytes = x.toXml()
    assert b"Test Song" in xml_bytes
    assert b"https://example.com/art.jpg" in xml_bytes

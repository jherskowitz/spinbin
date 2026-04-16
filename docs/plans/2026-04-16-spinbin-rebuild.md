# Spinbin Rebuild Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebuild Spinbin as a zero-cost, GitHub Actions-powered service that scrapes radio station playlists (starting with KEXP) and publishes XSPF files via GitHub Pages for Parachord to subscribe to.

**Architecture:** A Python script runs on a cron via GitHub Actions every 30 minutes. It fetches the last 24 hours of plays from the KEXP API, generates an XSPF playlist file, and commits it to the `gh-pages` branch. GitHub Pages serves the XSPF files as static content. The scraper framework is modular — each source is a Python module returning a list of track dicts, making it trivial to add new stations later.

**Tech Stack:** Python 3.12, `requests`, stdlib `xml.etree.ElementTree`, GitHub Actions, GitHub Pages

---

### Task 1: Initialize the Repository

**Files:**
- Create: `README.md`
- Create: `.gitignore`
- Create: `requirements.txt`

**Step 1: Initialize git repo and create `.gitignore`**

```bash
cd /Users/jherskowitz/Development/spinbin
git init
```

Create `.gitignore`:
```
__pycache__/
*.pyc
.env
venv/
output/
```

**Step 2: Create `requirements.txt`**

```
requests>=2.31.0
```

**Step 3: Create `README.md`**

```markdown
# Spinbin

Turning the web into playlists... one page at a time.

Spinbin scrapes radio station and chart playlists, generates XSPF playlist files, and publishes them via GitHub Pages. Subscribe in Parachord or any XSPF-compatible player.

## Playlists

| Playlist | XSPF URL | Source |
|----------|----------|--------|
| KEXP Today | `https://jherskowitz.github.io/spinbin/playlists/kexp-today.xspf` | [kexp.org](https://www.kexp.org/playlist/) |

## How It Works

A GitHub Actions workflow runs every 30 minutes, fetches playlist data from source APIs, generates XSPF files, and publishes them to GitHub Pages.
```

**Step 4: Commit**

```bash
git add .gitignore requirements.txt README.md
git commit -m "feat: initialize spinbin project"
```

---

### Task 2: Port the XSPF Generator to Python 3

The old `xspf.py` from the original spinbin is a solid XSPF library. Port it to Python 3.

**Files:**
- Create: `xspf.py`
- Create: `tests/test_xspf.py`

**Step 1: Write the failing test**

Create `tests/__init__.py` (empty) and `tests/test_xspf.py`:

```python
from xspf import Xspf


def test_empty_playlist_generates_valid_xml():
    x = Xspf()
    x.title = "Test Playlist"
    xml_bytes = x.toXml()
    assert b"<title" in xml_bytes or b":title" in xml_bytes
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
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/jherskowitz/Development/spinbin
python -m pytest tests/test_xspf.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'xspf'`

**Step 3: Port xspf.py to Python 3**

Create `xspf.py` — this is the original code with Python 3 fixes applied:
- `obj.items()` instead of `list(obj.items())` (already works)
- `ET.tostring` with `encoding="unicode"` returns str; use `encoding="utf-8"` for bytes
- Remove Python 2 print statements (none in xspf.py)
- Keep the `Xspf` and `Track` classes as-is — they're clean

```python
import xml.etree.ElementTree as ET


class XspfBase:
    NS = "http://xspf.org/ns/0/"

    def _addAttributesToXml(self, parent, attrs):
        for attr in attrs:
            value = getattr(self, attr)
            if value:
                el = ET.SubElement(parent, "{{{0}}}{1}".format(self.NS, attr))
                el.text = value


if hasattr(ET, "register_namespace"):
    ET.register_namespace("", XspfBase.NS)


def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class Xspf(XspfBase):
    def __init__(self, obj=None, **kwargs):
        self.version = "1"
        self._title = ""
        self._creator = ""
        self._info = ""
        self._annotation = ""
        self._location = ""
        self._identifier = ""
        self._image = ""
        self._date = ""
        self._license = ""
        self._trackList = []

        if obj:
            if "playlist" in obj:
                obj = obj["playlist"]
            for k, v in obj.items():
                setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def creator(self):
        return self._creator

    @creator.setter
    def creator(self, creator):
        self._creator = creator

    @property
    def annotation(self):
        return self._annotation

    @annotation.setter
    def annotation(self, annotation):
        self._annotation = annotation

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, info):
        self._info = info

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        self._location = location

    @property
    def identifier(self):
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = identifier

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, image):
        self._image = image

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date):
        self._date = date

    @property
    def license(self):
        return self._license

    @license.setter
    def license(self, license):
        self._license = license

    @property
    def track(self):
        return self._trackList

    @track.setter
    def track(self, track):
        self.add_track(track)

    def add_track(self, track=None, **kwargs):
        if track is None:
            track = {}
        if isinstance(track, list):
            for t in track:
                self.add_track(t)
        elif isinstance(track, Track):
            self._trackList.append(track)
        elif isinstance(track, dict) and len(track) > 0:
            self._trackList.append(Track(track))
        elif len(kwargs) > 0:
            self._trackList.append(Track(kwargs))

    def toXml(self, encoding="utf-8", pretty_print=True):
        root = ET.Element("{{{0}}}playlist".format(self.NS))
        root.set("version", self.version)
        self._addAttributesToXml(
            root,
            [
                "title", "info", "creator", "annotation",
                "location", "identifier", "image", "date", "license",
            ],
        )
        if len(self._trackList):
            track_list = ET.SubElement(root, "{{{0}}}trackList".format(self.NS))
            for track in self._trackList:
                track.getXmlObject(track_list)
        if pretty_print:
            indent(root)
        return ET.tostring(root, encoding)


class Track(XspfBase):
    def __init__(self, obj=None, **kwargs):
        self._location = ""
        self._identifier = ""
        self._title = ""
        self._creator = ""
        self._annotation = ""
        self._info = ""
        self._image = ""
        self._album = ""
        self._trackNum = ""
        self._duration = ""

        if obj:
            for k, v in obj.items():
                setattr(self, k, v)
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, location):
        self._location = location

    @property
    def identifier(self):
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = identifier

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title

    @property
    def creator(self):
        return self._creator

    @creator.setter
    def creator(self, creator):
        self._creator = creator

    @property
    def annotation(self):
        return self._annotation

    @annotation.setter
    def annotation(self, annotation):
        self._annotation = annotation

    @property
    def info(self):
        return self._info

    @info.setter
    def info(self, info):
        self._info = info

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, image):
        self._image = image

    @property
    def album(self):
        return self._album

    @album.setter
    def album(self, album):
        self._album = album

    @property
    def trackNum(self):
        return self._trackNum

    @trackNum.setter
    def trackNum(self, trackNum):
        self._trackNum = trackNum

    @property
    def duration(self):
        return self._duration

    @duration.setter
    def duration(self, duration):
        self._duration = duration

    def getXmlObject(self, parent):
        track = ET.SubElement(parent, "{{{0}}}track".format(self.NS))
        self._addAttributesToXml(
            track,
            [
                "location", "identifier", "title", "creator",
                "annotation", "info", "image", "album",
                "trackNum", "duration",
            ],
        )
        return parent
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_xspf.py -v
```

Expected: 3 PASS

**Step 5: Commit**

```bash
git add xspf.py tests/
git commit -m "feat: port xspf.py library to Python 3"
```

---

### Task 3: Build the KEXP Scraper

**Files:**
- Create: `scrapers/__init__.py`
- Create: `scrapers/kexp.py`
- Create: `tests/test_kexp.py`

**Step 1: Write the failing test**

Create `scrapers/__init__.py` (empty) and `tests/test_kexp.py`:

```python
import json
from unittest.mock import patch, MagicMock
from scrapers.kexp import fetch_plays, KEXP_API_URL


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
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_kexp.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'scrapers.kexp'`

**Step 3: Implement the KEXP scraper**

Create `scrapers/kexp.py`:

```python
import requests
from datetime import datetime, timedelta, timezone

KEXP_API_URL = "https://api.kexp.org/v2/plays/"


def fetch_plays(hours=24, limit=200):
    """Fetch KEXP plays from the last `hours` hours. Returns list of track dicts."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_str = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    all_tracks = []
    url = KEXP_API_URL
    params = {
        "format": "json",
        "limit": limit,
        "ordering": "-airdate",
        "begin_airdate": since_str,
    }

    while url:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        for play in data.get("results", []):
            if play.get("play_type") != "trackplay":
                continue
            if not play.get("song") or not play.get("artist"):
                continue
            all_tracks.append({
                "title": play["song"],
                "creator": play["artist"],
                "album": play.get("album") or "",
                "image": play.get("image_uri") or "",
            })

        url = data.get("next")
        params = None  # next URL includes params already

    return all_tracks
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_kexp.py -v
```

Expected: 2 PASS

**Step 5: Commit**

```bash
git add scrapers/ tests/test_kexp.py
git commit -m "feat: add KEXP playlist scraper"
```

---

### Task 4: Build the Main Generate Script

This is the script that GitHub Actions will call. It fetches tracks, generates XSPF, and writes it to the output directory.

**Files:**
- Create: `generate.py`
- Create: `tests/test_generate.py`

**Step 1: Write the failing test**

Create `tests/test_generate.py`:

```python
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
        # Should not write an empty playlist
        assert not os.path.exists(outfile)
```

**Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_generate.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'generate'`

**Step 3: Implement generate.py**

```python
import os
import sys
from datetime import datetime, timezone

from xspf import Xspf
from scrapers import kexp

PLAYLISTS = {
    "kexp": {
        "title": "KEXP: Today's Playlist",
        "filename": "kexp-today.xspf",
        "fetch": kexp.fetch_plays,
        "info": "https://www.kexp.org/playlist/",
    },
}


def generate_playlist(name, output_dir):
    config = PLAYLISTS[name]
    tracks = config["fetch"]()

    if not tracks:
        print(f"No tracks found for {name}, skipping.")
        return

    playlist = Xspf()
    playlist.title = config["title"]
    playlist.info = config["info"]
    playlist.date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    for track in tracks:
        playlist.add_track(
            title=track["title"],
            creator=track["creator"],
            album=track.get("album", ""),
            image=track.get("image", ""),
        )

    os.makedirs(output_dir, exist_ok=True)
    outpath = os.path.join(output_dir, config["filename"])
    with open(outpath, "wb") as f:
        f.write(playlist.toXml())
    print(f"Wrote {len(tracks)} tracks to {outpath}")


def main():
    output_dir = os.environ.get("OUTPUT_DIR", "output/playlists")
    for name in PLAYLISTS:
        generate_playlist(name, output_dir)


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_generate.py -v
```

Expected: 2 PASS

**Step 5: Commit**

```bash
git add generate.py tests/test_generate.py
git commit -m "feat: add playlist generation script"
```

---

### Task 5: Set Up GitHub Actions Workflow

**Files:**
- Create: `.github/workflows/generate.yml`

**Step 1: Create the workflow file**

```yaml
name: Generate Playlists

on:
  schedule:
    # Every 30 minutes
    - cron: '*/30 * * * *'
  workflow_dispatch: # Allow manual trigger

permissions:
  contents: write

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: python -m pytest tests/ -v

      - name: Generate playlists
        run: python generate.py
        env:
          OUTPUT_DIR: output/playlists

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./output
          keep_files: true
```

**Step 2: Commit**

```bash
git add .github/workflows/generate.yml
git commit -m "feat: add GitHub Actions workflow for playlist generation"
```

---

### Task 6: Configure GitHub Pages

**Step 1: Create initial gh-pages content**

The `peaceiris/actions-gh-pages` action will create the `gh-pages` branch automatically on first run. But we need a simple index page so the root URL isn't empty.

Create `output/index.html`:

```html
<!DOCTYPE html>
<html>
<head><title>Spinbin</title></head>
<body>
<h1>Spinbin</h1>
<p>Turning the web into playlists... one page at a time.</p>
<h2>Available Playlists</h2>
<ul>
  <li><a href="playlists/kexp-today.xspf">KEXP: Today's Playlist</a></li>
</ul>
</body>
</html>
```

**Step 2: Commit**

```bash
git add output/index.html
git commit -m "feat: add index page for GitHub Pages"
```

---

### Task 7: Push to GitHub and Enable Pages

**Step 1: Create the repo on GitHub**

```bash
gh repo create jherskowitz/spinbin --public --source=. --push
```

Note: This will push the existing local repo. If the remote already exists (from the old spinbin), we may need to force-push or create a fresh repo. The old repo can be archived first.

**Step 2: Enable GitHub Pages**

```bash
gh api repos/jherskowitz/spinbin/pages -X POST -f source.branch=gh-pages -f source.path=/
```

Or if Pages is already enabled, update it:
```bash
gh api repos/jherskowitz/spinbin/pages -X PUT -f source.branch=gh-pages -f source.path=/
```

**Step 3: Trigger the workflow manually for the first run**

```bash
gh workflow run generate.yml
```

**Step 4: Verify the XSPF is accessible**

Wait for the workflow to complete, then verify:
```bash
curl -s https://jherskowitz.github.io/spinbin/playlists/kexp-today.xspf | head -20
```

Expected: Valid XSPF XML with KEXP track data.

---

### Task 8: Test End-to-End Locally

Before pushing, verify the full pipeline works locally.

**Step 1: Install dependencies**

```bash
cd /Users/jherskowitz/Development/spinbin
pip install -r requirements.txt
```

**Step 2: Run all tests**

```bash
python -m pytest tests/ -v
```

Expected: All tests pass.

**Step 3: Run generate.py and inspect output**

```bash
python generate.py
cat output/playlists/kexp-today.xspf | head -40
```

Expected: Valid XSPF with real KEXP tracks from today.

**Step 4: Commit any final adjustments**

---

## Adding New Sources Later

To add a new radio station or chart source:

1. Create `scrapers/newstation.py` with a `fetch_plays()` function returning `[{"title": ..., "creator": ..., "album": ..., "image": ...}]`
2. Add an entry to the `PLAYLISTS` dict in `generate.py`
3. Add tests in `tests/test_newstation.py`
4. Update `output/index.html` and `README.md`

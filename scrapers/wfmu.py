import re
import html
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser

WFMU_FEED_URL = "https://wfmu.org/playlistfeed.xml"


def _strip_tags(s):
    """Remove HTML tags and normalize whitespace.

    WFMU's song_title cells contain the visible title plus extra junk:
    a '<button>→</button>' (jump-to-comment arrow) and a hidden
    '<span style="display:none" id="..._summary_html">"Title" by "Artist"</span>'
    used by their JS for tooltips. Naive tag-stripping concatenates all of
    these, producing 'Friday I'm in Love → "Friday I'm in Love" by "The Cure"'.
    Strip those wrappers first, then the remaining tags.
    """
    if not s:
        return ""
    # Drop hidden spans (the summary_html duplicates) entirely.
    s = re.sub(
        r'<span[^>]*style="[^"]*display\s*:\s*none[^"]*"[^>]*>.*?</span>',
        "",
        s,
        flags=re.DOTALL | re.IGNORECASE,
    )
    # Drop buttons (they contain glyphs like → that would leak in).
    s = re.sub(r"<button\b[^>]*>.*?</button>", " ", s, flags=re.DOTALL | re.IGNORECASE)
    # Strip remaining tags and normalize whitespace.
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def _parse_show_tracks(html_text):
    """Extract tracks from a WFMU show playlist page.

    WFMU show pages contain a table with id='drop_table'. Each row with a
    class containing 'track' (or with both artist and song cells populated)
    represents a played track.
    """
    # Find the drop_table
    m = re.search(r'<table[^>]*id="drop_table"[^>]*>(.*?)</table>', html_text, re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    table = m.group(1)

    tracks = []
    # Parse each <tr>...</tr>
    for row in re.finditer(r'<tr[^>]*>(.*?)</tr>', table, re.DOTALL | re.IGNORECASE):
        row_html = row.group(1)
        # Skip header rows
        if '<th' in row_html.lower():
            continue

        cells = {}
        for cell in re.finditer(r'<td[^>]*class="[^"]*col_(\w+)[^"]*"[^>]*>(.*?)</td>', row_html, re.DOTALL | re.IGNORECASE):
            key = cell.group(1)
            cells[key] = _strip_tags(cell.group(2))

        artist = cells.get("artist", "")
        song = cells.get("song_title", "")
        album = cells.get("album_title", "")

        # Skip set-break or DJ-chat rows (they have "Music behind DJ" or blank artist)
        if not artist or not song:
            continue
        if "music behind dj" in artist.lower():
            continue

        tracks.append({
            "title": song,
            "creator": artist,
            "album": album,
            "image": "",
        })

    return tracks


def fetch_plays(hours=24, max_shows=8):
    """Fetch WFMU tracks from recent shows in their RSS feed.

    WFMU doesn't expose a JSON API, so we:
      1. Fetch the RSS feed of recent show playlists
      2. Filter to shows within the last `hours` hours
      3. Scrape each show's HTML page for its track list (capped at `max_shows`)
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    headers = {"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"}

    resp = requests.get(WFMU_FEED_URL, timeout=30, headers=headers)
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    channel = root.find("channel")
    if channel is None:
        return []

    show_urls = []
    for item in channel.findall("item"):
        link = (item.findtext("link") or "").strip()
        pub = item.findtext("pubDate")
        if not link or not pub:
            continue
        try:
            pub_dt = dateparser.parse(pub)
            if pub_dt.tzinfo is None:
                pub_dt = pub_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        if pub_dt < since:
            continue
        show_urls.append(link)
        if len(show_urls) >= max_shows:
            break

    all_tracks = []
    for url in show_urls:
        try:
            r = requests.get(url, timeout=30, headers=headers)
            r.raise_for_status()
        except requests.RequestException:
            continue
        all_tracks.extend(_parse_show_tracks(r.text))

    return all_tracks

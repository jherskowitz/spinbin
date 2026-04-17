import re
import html
import requests

XRAY_PLAYLIST_URL = "https://xray.fm/playlist"


def _strip_tags(s):
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    # Replace non-breaking spaces
    s = s.replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()


def _parse_rows(html_text):
    """Parse the <tr class="track"> rows from XRAY's playlist HTML."""
    tracks = []
    for row in re.finditer(r'<tr[^>]*class="[^"]*\btrack\b[^"]*"[^>]*>(.*?)</tr>', html_text, re.DOTALL | re.IGNORECASE):
        body = row.group(1)
        cells = {}
        for cell in re.finditer(
            r'<t[dh][^>]*class="[^"]*\btrack-(\w+)\b[^"]*"[^>]*>(.*?)</t[dh]>',
            body,
            re.DOTALL | re.IGNORECASE,
        ):
            cells[cell.group(1)] = _strip_tags(cell.group(2))

        artist = cells.get("artist", "")
        title = cells.get("title", "")
        if not artist or not title:
            continue

        tracks.append({
            "title": title,
            "creator": artist,
            "album": cells.get("album", ""),
            "image": "",
        })

    return tracks


def fetch_plays(hours=24):
    """Fetch the recent tracks from XRAY.fm's public playlist page.

    XRAY.fm (Portland community radio) renders their playlist server-side
    as an HTML table at `/playlist`. Each row has class `track` with cells
    `track-artist`, `track-title`, `track-album`. The page shows roughly
    the most recent 20 plays; `hours` is accepted for API consistency but
    doesn't change anything since the page itself is fixed-size.
    """
    resp = requests.get(
        XRAY_PLAYLIST_URL,
        timeout=30,
        headers={"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"},
    )
    resp.raise_for_status()
    return _parse_rows(resp.text)

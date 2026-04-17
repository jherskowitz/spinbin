import re
import html
import requests

XRAY_PLAYLIST_URL = "https://xray.fm/playlist"
XRAY_PAGE_URL = "https://xray.fm/tracks/index/page:{page}?url=playlist"
DEFAULT_MAX_PAGES = 15  # ~300 tracks, typically ~24h of continuous programming
HEADERS = {"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"}


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


def fetch_plays(hours=24, max_pages=DEFAULT_MAX_PAGES):
    """Fetch recent tracks from XRAY.fm by paginating through their playlist.

    XRAY.fm (Portland community radio) renders a server-side playlist at
    `/playlist` showing the most recent 20 tracks, with pagination at
    `/tracks/index/page:N?url=playlist`. We fetch up to `max_pages` pages
    (roughly `max_pages * 20` tracks) — 15 pages is about a day's worth.

    `hours` is accepted for API consistency but XRAY doesn't expose per-track
    timestamps with dates, so we can't filter precisely — we rely on the
    page cap instead.
    """
    all_tracks = []
    for page in range(1, max_pages + 1):
        url = XRAY_PLAYLIST_URL if page == 1 else XRAY_PAGE_URL.format(page=page)
        try:
            resp = requests.get(url, timeout=30, headers=HEADERS)
            resp.raise_for_status()
        except requests.RequestException:
            break

        page_tracks = _parse_rows(resp.text)
        if not page_tracks:
            break

        all_tracks.extend(page_tracks)

    return all_tracks

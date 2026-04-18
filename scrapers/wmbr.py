"""WMBR (MIT 88.1 FM) recent plays scraper.

WMBR doesn't use Spinitron. They publish a tiny XML endpoint at
`/dynamic.xml` that powers their homepage 'now playing' widget. The
`<wmbr_plays>` element contains an HTML-encoded fragment of recent
plays like:

    <p class="recent">7:45p&nbsp;<b>Artist Name</b>: Song Title</p>

We unescape the fragment, extract the artist/title pairs, and return
them newest-first.
"""
import html
import re

import requests

WMBR_DYNAMIC_URL = "https://wmbr.org/dynamic.xml"
HEADERS = {"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"}

_WMBR_PLAYS_TAG = re.compile(r"<wmbr_plays>(.*?)</wmbr_plays>", re.DOTALL)
_RECENT_P = re.compile(
    r'<p class="recent">.*?<b>(?P<artist>.*?)</b>\s*:\s*(?P<title>.*?)</p>',
    re.DOTALL,
)


def fetch_plays(hours=24):
    """Fetch recent plays from WMBR's dynamic.xml feed.

    `hours` is accepted for API consistency. WMBR's feed doesn't include
    per-track timestamps in machine-readable form (just a "7:45p"-style
    time prefix), so we return every track in the current fragment —
    typically the last hour of programming.
    """
    resp = requests.get(WMBR_DYNAMIC_URL, timeout=30, headers=HEADERS)
    resp.raise_for_status()

    # The outer file is XML. The <wmbr_plays> element's *contents* are
    # HTML-encoded HTML, not real XML children — so extract the string
    # content and decode it once.
    m = _WMBR_PLAYS_TAG.search(resp.text)
    if not m:
        return []

    inner_html = html.unescape(m.group(1))

    tracks = []
    for row in _RECENT_P.finditer(inner_html):
        artist = _clean(row.group("artist"))
        title = _clean(row.group("title"))
        if not artist or not title:
            continue
        tracks.append({
            "title": title,
            "creator": artist,
            "album": "",
            "image": "",
        })

    return tracks


def _clean(s):
    """Strip nested tags and normalize whitespace."""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s)
    # nbsp → space
    s = s.replace("\xa0", " ")
    return re.sub(r"\s+", " ", s).strip()

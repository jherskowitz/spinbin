"""Spinitron scraper: parses embedded `data-spin` JSON from station pages.

Spinitron hosts public now-playing pages for hundreds of non-commercial
radio stations at `spinitron.com/{STATION}/`. Each spin on the page carries
a `data-spin="{json}"` attribute with fields:
  a = artist, s = song title, r = release/album, i = identifier

Since the page only renders the most recent ~15–30 spins and pagination
URL params don't increase the count, we take whatever is on the page
when the job runs. For a once-daily cron this yields the station's
current hour of plays — small but high-signal.
"""
import html
import json
import re

import requests

SPINITRON_URL = "https://spinitron.com/{station}/"
HEADERS = {"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"}

# Matches each data-spin="{…}" attribute; value is HTML-entity-encoded JSON.
_SPIN_RE = re.compile(r'data-spin="([^"]+)"')


def fetch_plays(station, hours=24):
    """Fetch recent tracks for a Spinitron-hosted station.

    Args:
        station: The station's Spinitron slug (e.g. "WPRB", "KALX").
        hours: Accepted for API consistency. Spinitron's public page
            doesn't expose per-spin timestamps to the client, so we return
            everything rendered on the page.

    Returns a list of track dicts with title/creator/album/image keys.
    """
    resp = requests.get(
        SPINITRON_URL.format(station=station),
        timeout=30,
        headers=HEADERS,
    )
    resp.raise_for_status()

    tracks = []
    seen = set()
    for match in _SPIN_RE.finditer(resp.text):
        raw = html.unescape(match.group(1))
        try:
            spin = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue

        artist = (spin.get("a") or "").strip()
        title = (spin.get("s") or "").strip()
        album = (spin.get("r") or "").strip()
        if not artist or not title:
            continue

        # De-dupe the same spin if it shows up twice on a page
        key = (artist, title)
        if key in seen:
            continue
        seen.add(key)

        tracks.append({
            "title": title,
            "creator": artist,
            "album": album,
            "image": "",
        })

    return tracks

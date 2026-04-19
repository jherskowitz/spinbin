"""OnlineRadioBox scraper.

OnlineRadioBox tracks recently-played metadata for thousands of stations
worldwide and exposes it through the JSON feed used by their embeddable
"playlist widget":

    https://onlineradiobox.com/json/{country}/{slug}/playlist/{day}?tz=0

Where `day=0` is today and `day=1..6` are the previous days. Entries:

    {"id": "...", "name": "Artist - Song", "created": 1776557028}

Not every station on OnlineRadioBox has rich data — some only track the
current track periodically — but many (including Bagel Radio, which uses
this via SoundStack's widget) do.
"""
import re
import requests
from datetime import datetime, timedelta, timezone

ORB_URL = "https://onlineradiobox.com/json/{country}/{slug}/playlist/{day}"
HEADERS = {"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"}
SEP_RE = re.compile(r"\s+-\s+")


def _split_artist_title(name):
    """Split 'Artist - Song' on the first hyphen with surrounding spaces."""
    m = SEP_RE.search(name or "")
    if not m:
        return "", (name or "").strip()
    return name[: m.start()].strip(), name[m.end():].strip()


def fetch_plays(country, slug, hours=24, days_back=2):
    """Fetch recent plays for an OnlineRadioBox-tracked station.

    Args:
        country: Country code in their URL scheme (e.g. "us", "uk").
        slug: Station slug (e.g. "bagel" for Bagel Radio).
        hours: Filter tracks to the last N hours (based on `created` epoch).
        days_back: How many days of the feed to fetch. The API returns one
            day at a time; fetching today + yesterday covers a 24h window
            regardless of what time the cron runs.

    Returns list of track dicts.
    """
    since_ts = (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp()

    all_entries = []
    for day in range(days_back):
        url = ORB_URL.format(country=country, slug=slug, day=day)
        try:
            resp = requests.get(url, params={"tz": 0}, timeout=30, headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError):
            continue
        for e in data.get("playlist") or []:
            all_entries.append(e)

    # De-dupe by id (stable across days when present) and preserve newest-first
    seen_ids = set()
    all_entries.sort(key=lambda e: e.get("created") or 0, reverse=True)

    tracks = []
    for entry in all_entries:
        name = entry.get("name") or ""
        created = entry.get("created") or 0
        if not name or not created:
            continue
        if created < since_ts:
            continue

        entry_id = entry.get("id")
        key = entry_id or (name, created)
        if key in seen_ids:
            continue
        seen_ids.add(key)

        artist, title = _split_artist_title(name)
        if not title:
            continue
        if not artist:
            # Fall back to station slug as creator when name has no separator
            artist = slug

        tracks.append({
            "title": title,
            "creator": artist,
            "album": "",
            "image": "",
        })

    return tracks

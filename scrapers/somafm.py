import requests
from datetime import datetime, timedelta, timezone

SOMAFM_SONGS_URL = "https://somafm.com/songs/{channel}.json"
DEFAULT_CHANNEL = "groovesalad"


def fetch_plays(channel=DEFAULT_CHANNEL, hours=24):
    """Fetch SomaFM plays for a channel. Returns list of track dicts.

    SomaFM only exposes ~20 recent tracks per channel. We filter to the last
    `hours` hours based on each track's `date` field (unix timestamp).
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    since_ts = since.timestamp()

    url = SOMAFM_SONGS_URL.format(channel=channel)
    resp = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"},
    )
    resp.raise_for_status()
    data = resp.json()

    tracks = []
    for song in data.get("songs", []):
        artist = song.get("artist") or ""
        title = song.get("title") or ""
        if not artist or not title:
            continue

        # Filter by timestamp
        try:
            ts = float(song.get("date", "0"))
        except (TypeError, ValueError):
            ts = 0
        if ts and ts < since_ts:
            continue

        tracks.append({
            "title": title,
            "creator": artist,
            "album": song.get("album") or "",
            "image": song.get("albumArt") or "",
        })

    return tracks

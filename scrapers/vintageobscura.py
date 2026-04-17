import requests
from datetime import datetime, timedelta, timezone

VO_JSON_URL = "https://vintageobscura.net/station_meta/recent_tracks.json"
HEADERS = {"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"}


def _split_artist_title(combined):
    """Split 'Artist - Song [metadata]' into (artist, song-with-metadata).

    Vintage Obscura titles follow the convention 'Artist Name - Song Title
    [country, genre] (year)'. We split on the first ' - ' to get a clean
    artist, and keep everything after as the track title (preserving the
    descriptive metadata, which users find useful).
    """
    if not combined:
        return "", ""
    sep = " - "
    idx = combined.find(sep)
    if idx < 0:
        return "", combined.strip()
    artist = combined[:idx].strip()
    title = combined[idx + len(sep):].strip()
    return artist, title


def fetch_plays(hours=24):
    """Fetch Vintage Obscura's recent tracks feed.

    Vintage Obscura is a streaming radio station showcasing rare vintage
    tracks from around the world, curated from r/vintageobscura submissions.
    Their `recent_tracks.json` endpoint powers the homepage's now-playing
    widget and contains the current rotation.
    """
    resp = requests.get(VO_JSON_URL, timeout=30, headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()

    since_ts = (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp()

    tracks = []
    for entry in data:
        combined = entry.get("title") or ""
        if not combined:
            continue

        # Optional time-window filter using start_timestamp (unix seconds).
        ts = entry.get("start_timestamp")
        if isinstance(ts, (int, float)) and ts and ts < since_ts:
            continue

        artist, title = _split_artist_title(combined)
        if not title:
            continue
        # If there's no ' - ', fall back to using the genre/show as creator
        if not artist:
            artist = entry.get("show") or "Vintage Obscura"

        tracks.append({
            "title": title,
            "creator": artist,
            "album": entry.get("show") or "",
            "image": entry.get("img") or "",
        })

    return tracks

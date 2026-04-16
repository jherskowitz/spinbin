import requests
from datetime import datetime, timedelta, timezone

KCRW_API_URL = "https://tracklist-api.kcrw.com/Simulcast/date"


def fetch_plays(hours=24):
    """Fetch KCRW Simulcast plays from the last `hours` hours. Returns list of track dicts."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    all_tracks = []

    # KCRW API is date-based (YYYY/MM/DD), so collect all dates we need
    dates = set()
    current = since
    while current <= now:
        dates.add(current.strftime("%Y/%m/%d"))
        current += timedelta(days=1)

    for date_str in sorted(dates, reverse=True):
        url = f"{KCRW_API_URL}/{date_str}"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            plays = resp.json()
        except (requests.RequestException, ValueError):
            continue

        for play in plays:
            # Filter out breaks
            artist = play.get("artist") or ""
            if not artist or artist == "[BREAK]":
                continue
            title = play.get("title")
            if not title:
                continue

            all_tracks.append({
                "title": title,
                "creator": artist,
                "album": play.get("album") or "",
                "image": play.get("albumImageLarge") or play.get("albumImage") or "",
            })

    return all_tracks

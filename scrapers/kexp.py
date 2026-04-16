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

import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser

KEXP_API_URL = "https://api.kexp.org/v2/plays/"
MAX_PAGES = 10  # Safety cap to prevent runaway pagination


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

    pages_fetched = 0
    done = False

    while url and not done and pages_fetched < MAX_PAGES:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        pages_fetched += 1

        for play in data.get("results", []):
            # Check if we've gone past the time window
            airdate_str = play.get("airdate")
            if airdate_str:
                airdate = dateparser.parse(airdate_str)
                if airdate.tzinfo is None:
                    airdate = airdate.replace(tzinfo=timezone.utc)
                if airdate < since:
                    done = True
                    break

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

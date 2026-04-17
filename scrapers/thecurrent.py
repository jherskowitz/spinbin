import requests

CURRENT_API_URL = "https://www.thecurrent.org/api/songs/the-current"


def fetch_plays(hours=24):
    """Fetch The Current (KCMP 89.3) recent plays via their songs API.

    The Current's public API is at `/api/songs/the-current`. It historically
    returned the recent playlist but at time of writing returns an empty
    `{"songs":[]}` response — the scraper handles this gracefully by
    returning an empty list (generate.py then skips writing the XSPF).
    """
    resp = requests.get(
        CURRENT_API_URL,
        timeout=30,
        headers={"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"},
    )
    resp.raise_for_status()
    data = resp.json()

    tracks = []
    for song in data.get("songs", []):
        title = song.get("title") or song.get("name") or ""
        artist = song.get("artist") or song.get("artistName") or ""
        if not title or not artist:
            continue
        tracks.append({
            "title": title,
            "creator": artist,
            "album": song.get("album") or "",
            "image": song.get("albumArt") or song.get("image") or "",
        })

    return tracks

import requests
from datetime import datetime, timedelta, timezone

RP_API_URL = "https://api.radioparadise.com/api/nowplaying_list"
HEADERS = {"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"}


def fetch_plays(channel=0, hours=24, list_num=100):
    """Fetch recent tracks from Radio Paradise.

    Radio Paradise is a subscriber-supported internet radio station with
    meticulous human curation across four channels:
      0 = Main Mix, 1 = Mellow Mix, 2 = Rock Mix, 3 = World/Etc Mix

    Their API returns the recent tracklist as an object keyed by index
    under a `song` field. `list_num` controls how many to request — the
    API honors values up to a few hundred.
    """
    resp = requests.get(
        RP_API_URL,
        params={"chan": channel, "list_num": list_num},
        timeout=30,
        headers=HEADERS,
    )
    resp.raise_for_status()
    data = resp.json()

    songs_obj = data.get("song") or {}
    since_ts = (datetime.now(timezone.utc) - timedelta(hours=hours)).timestamp()

    tracks = []
    # RP returns `song` as an object keyed by integer strings ("0", "1", ...)
    # preserving insertion order (newest first)
    for key in sorted(songs_obj.keys(), key=lambda k: int(k) if k.isdigit() else 0):
        song = songs_obj[key]
        if not isinstance(song, dict):
            continue
        title = song.get("title") or ""
        artist = song.get("artist") or ""
        if not title or not artist:
            continue

        # Filter by sched_time (unix seconds)
        try:
            ts = int(song.get("sched_time", 0))
        except (TypeError, ValueError):
            ts = 0
        if ts and ts < since_ts:
            continue

        cover = song.get("cover") or ""
        # Cover URLs are relative to RP's CDN
        if cover and not cover.startswith("http"):
            cover = f"https://img.radioparadise.com/{cover}"

        tracks.append({
            "title": title,
            "creator": artist,
            "album": song.get("album") or "",
            "image": cover,
        })

    return tracks

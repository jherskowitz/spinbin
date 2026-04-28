"""xmplaylist.com scraper.

xmplaylist.com is a third-party aggregator that monitors SiriusXM
channels and publishes their recently-played tracks. They expose a clean
public JSON endpoint:

    https://xmplaylist.com/api/station/{slug}

with cursor-style pagination via a `next` URL using `?last=<unix-ms>`.
This one scraper works for any SiriusXM channel xmplaylist tracks
(Sirius XMU, Alt Nation, Lithium, Octane, The Bridge, etc.).
"""
import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser

API_URL = "https://xmplaylist.com/api/station/{station}"
HEADERS = {"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"}
MAX_PAGES = 12  # Safety cap. ~24 results/page → ~288 tracks max.


def fetch_plays(station, hours=24):
    """Fetch recent plays from an xmplaylist-tracked SiriusXM channel.

    Args:
        station: xmplaylist's station slug (e.g. "siriusxmu", "altnation").
        hours: Filter tracks to the last N hours by `timestamp`.

    Returns list of track dicts with title/creator/album/image.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    url = API_URL.format(station=station)
    tracks = []
    pages = 0
    seen_ids = set()
    done = False

    while url and not done and pages < MAX_PAGES:
        try:
            resp = requests.get(url, timeout=30, headers=HEADERS)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError):
            break

        pages += 1

        for entry in data.get("results") or []:
            ts_str = entry.get("timestamp")
            if ts_str:
                try:
                    ts = dateparser.parse(ts_str)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    ts = None
                if ts and ts < since:
                    done = True
                    break

            entry_id = entry.get("id")
            if entry_id and entry_id in seen_ids:
                continue
            if entry_id:
                seen_ids.add(entry_id)

            track = entry.get("track") or {}
            title = (track.get("title") or "").strip()
            artists = track.get("artists") or []
            artist = ", ".join(a.strip() for a in artists if a and a.strip())
            if not title or not artist:
                continue

            spotify = entry.get("spotify") or {}
            image = (
                spotify.get("albumImageMedium")
                or spotify.get("albumImageLarge")
                or spotify.get("albumImageSmall")
                or ""
            )

            tracks.append({
                "title": title,
                "creator": artist,
                "album": "",
                "image": image,
            })

        url = data.get("next")

    return tracks

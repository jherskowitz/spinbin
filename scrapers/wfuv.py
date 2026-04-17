import re
import requests
import xml.etree.ElementTree as ET

WFUV_FEED_URL = "https://wfuv.org/playlist/feed"


def fetch_plays(hours=24):
    """Fetch WFUV recent plays from their RSS feed.

    Returns list of track dicts. Note: WFUV's feed doesn't include album
    artwork or album names — only song title, artist, and play time.
    The feed includes only the most recent ~50 plays so the `hours`
    parameter is best-effort; we return everything in the feed.
    """
    resp = requests.get(
        WFUV_FEED_URL,
        timeout=30,
        headers={"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"},
    )
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    channel = root.find("channel")
    if channel is None:
        return []

    tracks = []
    for item in channel.findall("item"):
        title = (item.findtext("title") or "").strip()
        creator = (item.findtext("description") or "").strip()
        # Strip HTML tags that sometimes leak into description
        creator = re.sub(r"<[^>]+>", "", creator).strip()

        if not title or not creator:
            continue

        tracks.append({
            "title": title,
            "creator": creator,
            "album": "",
            "image": "",
        })

    return tracks

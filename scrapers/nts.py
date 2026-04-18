import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser

NTS_LIVE_URL = "https://www.nts.live/api/v2/live"
HEADERS = {"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"}


def _extract_tracklist_link(episode_details):
    """Find the `tracklist` link in a show episode's details object."""
    for link in (episode_details or {}).get("links") or []:
        if link.get("rel") == "tracklist":
            return link.get("href")
    return None


def _extract_episode_image(episode_details):
    media = (episode_details or {}).get("media") or {}
    return (
        media.get("picture_medium")
        or media.get("picture_medium_large")
        or media.get("background_medium")
        or ""
    )


def fetch_plays(hours=24):
    """Fetch tracks from NTS Radio's currently-airing shows.

    NTS exposes a `/api/v2/live` endpoint listing the current show on each
    of their two channels. Each show has a `tracklist` link returning the
    tracks DJs have submitted. Tracklist submission is DJ-dependent, so
    shows may return empty — we gather whatever is available from both
    live channels at scrape time.

    `hours` is accepted for API consistency but NTS doesn't expose
    per-track timestamps; we rely on capturing whatever shows are live at
    run-time (once a day = two shows captured).
    """
    resp = requests.get(NTS_LIVE_URL, timeout=30, headers=HEADERS)
    resp.raise_for_status()
    live = resp.json()

    all_tracks = []
    seen_urls = set()

    for channel in live.get("results") or []:
        now_block = channel.get("now") or {}
        details = (now_block.get("embeds") or {}).get("details") or {}

        tracklist_url = _extract_tracklist_link(details)
        if not tracklist_url or tracklist_url in seen_urls:
            continue
        seen_urls.add(tracklist_url)

        image = _extract_episode_image(details)
        show_name = details.get("name") or now_block.get("broadcast_title") or "NTS Radio"

        try:
            tl_resp = requests.get(tracklist_url, timeout=30, headers=HEADERS)
            tl_resp.raise_for_status()
            tl = tl_resp.json()
        except (requests.RequestException, ValueError):
            continue

        for entry in tl.get("results") or []:
            artist = (entry.get("artist") or "").strip()
            title = (entry.get("title") or "").strip()
            if not artist or not title:
                continue
            all_tracks.append({
                "title": title,
                "creator": artist,
                "album": show_name,
                "image": image,
            })

    return all_tracks

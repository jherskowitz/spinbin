import html
import os
import re
from datetime import datetime, timezone

from xspf import Xspf
from scrapers import kexp, kcrw, wfmu, wfuv, somafm, xrayfm

PLAYLISTS = {
    "kexp": {
        "title": "KEXP Rewind",
        "creator": "kexp.org",
        "filename": "kexp-today.xspf",
        "fetch": lambda: kexp.fetch_plays(),
        "info": "https://www.kexp.org/playlist/",
    },
    "kcrw": {
        "title": "KCRW Rewind",
        "creator": "kcrw.com",
        "filename": "kcrw-today.xspf",
        "fetch": lambda: kcrw.fetch_plays(),
        "info": "https://www.kcrw.com/playlists?channel=Simulcast",
    },
    "wfmu": {
        "title": "WFMU Rewind",
        "creator": "wfmu.org",
        "filename": "wfmu-today.xspf",
        "fetch": lambda: wfmu.fetch_plays(),
        "info": "https://wfmu.org/playlists/",
    },
    "wfuv": {
        "title": "WFUV Rewind",
        "creator": "wfuv.org",
        "filename": "wfuv-today.xspf",
        "fetch": lambda: wfuv.fetch_plays(),
        "info": "https://wfuv.org/playlist",
    },
    "somafm": {
        "title": "SomaFM Groove Salad Rewind",
        "creator": "somafm.com",
        "filename": "somafm-groovesalad-today.xspf",
        "fetch": lambda: somafm.fetch_plays(channel="groovesalad"),
        "info": "https://somafm.com/groovesalad/",
    },
    "xrayfm": {
        "title": "XRAY.fm Rewind",
        "creator": "xray.fm",
        "filename": "xrayfm-today.xspf",
        "fetch": lambda: xrayfm.fetch_plays(),
        "info": "https://xray.fm/playlist",
    },
}


def _clean(value):
    """Normalize scraper-provided text.

    - Decode HTML entities (`&amp;` → `&`, `&#39;` → `'`, etc.). Many radio
      station feeds deliver metadata pre-encoded, which — combined with our
      XML writer re-encoding it — results in `&amp;` appearing literally in
      downstream players.
    - Collapse repeated whitespace.
    - Strip leading/trailing whitespace.
    """
    if not value:
        return ""
    # Unescape repeatedly in case the source is double-encoded
    prev = None
    cur = str(value)
    while cur != prev:
        prev = cur
        cur = html.unescape(cur)
    return re.sub(r"\s+", " ", cur).strip()


def generate_playlist(name, output_dir):
    config = PLAYLISTS[name]
    tracks = config["fetch"]()

    if not tracks:
        print(f"No tracks found for {name}, skipping.")
        return

    playlist = Xspf()
    playlist.title = config["title"]
    playlist.creator = config["creator"]
    playlist.info = config["info"]
    playlist.date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    for track in tracks:
        playlist.add_track(
            title=_clean(track["title"]),
            creator=_clean(track["creator"]),
            album=_clean(track.get("album", "")),
            image=(track.get("image") or "").strip(),
        )

    os.makedirs(output_dir, exist_ok=True)
    outpath = os.path.join(output_dir, config["filename"])
    with open(outpath, "wb") as f:
        f.write(playlist.toXml())
    print(f"Wrote {len(tracks)} tracks to {outpath}")


def main():
    output_dir = os.environ.get("OUTPUT_DIR", "output/playlists")
    for name in PLAYLISTS:
        generate_playlist(name, output_dir)


if __name__ == "__main__":
    main()

import html
import os
import re
from datetime import datetime, timezone

from xspf import Xspf
from scrapers import (
    kexp,
    kcrw,
    wfmu,
    wfuv,
    wmbr,
    somafm,
    xrayfm,
    vintageobscura,
    radioparadise,
    nts,
    spinitron,
    onlineradiobox,
    xmplaylist,
)

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
    "somafm_indiepop": {
        "title": "SomaFM Indie Pop Rocks! Rewind",
        "creator": "somafm.com",
        "filename": "somafm-indiepop-today.xspf",
        "fetch": lambda: somafm.fetch_plays(channel="indiepop"),
        "info": "https://somafm.com/indiepop/",
    },
    "xrayfm": {
        "title": "XRAY.fm Rewind",
        "creator": "xray.fm",
        "filename": "xrayfm-today.xspf",
        "fetch": lambda: xrayfm.fetch_plays(),
        "info": "https://xray.fm/playlist",
    },
    "vintageobscura": {
        "title": "Vintage Obscura Rewind",
        "creator": "vintageobscura.net",
        "filename": "vintageobscura-today.xspf",
        "fetch": lambda: vintageobscura.fetch_plays(),
        "info": "https://vintageobscura.net/",
    },
    "radioparadise": {
        "title": "Radio Paradise Rewind",
        "creator": "radioparadise.com",
        "filename": "radioparadise-today.xspf",
        "fetch": lambda: radioparadise.fetch_plays(),
        "info": "https://radioparadise.com/",
    },
    "nts": {
        "title": "NTS Radio Rewind",
        "creator": "nts.live",
        "filename": "nts-today.xspf",
        "fetch": lambda: nts.fetch_plays(),
        "info": "https://www.nts.live/",
    },
    "wprb": {
        "title": "WPRB Rewind",
        "creator": "wprb.com",
        "filename": "wprb-today.xspf",
        "fetch": lambda: spinitron.fetch_plays("WPRB"),
        "info": "https://spinitron.com/WPRB/",
    },
    "kalx": {
        "title": "KALX Rewind",
        "creator": "kalx.berkeley.edu",
        "filename": "kalx-today.xspf",
        "fetch": lambda: spinitron.fetch_plays("KALX"),
        "info": "https://spinitron.com/KALX/",
    },
    "wmbr": {
        "title": "WMBR Rewind",
        "creator": "wmbr.org",
        "filename": "wmbr-today.xspf",
        "fetch": lambda: wmbr.fetch_plays(),
        "info": "https://wmbr.org/",
    },
    "bagelradio": {
        "title": "Bagel Radio Rewind",
        "creator": "bagelradio.com",
        "filename": "bagelradio-today.xspf",
        "fetch": lambda: onlineradiobox.fetch_plays("us", "bagel"),
        "info": "https://bagelradio.com/",
    },
    "siriusxmu": {
        "title": "SiriusXMU Rewind",
        "creator": "siriusxm.com",
        "filename": "siriusxmu-today.xspf",
        "fetch": lambda: xmplaylist.fetch_plays("siriusxmu"),
        "info": "https://xmplaylist.com/station/siriusxmu",
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

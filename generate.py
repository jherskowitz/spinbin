import os
from datetime import datetime, timezone

from xspf import Xspf
from scrapers import kexp, kcrw, wfmu, thecurrent, wfuv, somafm

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
    "thecurrent": {
        "title": "The Current Rewind",
        "creator": "thecurrent.org",
        "filename": "thecurrent-today.xspf",
        "fetch": lambda: thecurrent.fetch_plays(),
        "info": "https://www.thecurrent.org/playlist/the-current",
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
}


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
            title=track["title"],
            creator=track["creator"],
            album=track.get("album", ""),
            image=track.get("image", ""),
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

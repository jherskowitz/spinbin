import os
from datetime import datetime, timezone

from xspf import Xspf
from scrapers import kexp, kcrw

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

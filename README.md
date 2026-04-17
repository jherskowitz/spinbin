# Spinbin

Turning the web into playlists... one page at a time.

Spinbin scrapes radio station and chart playlists, generates XSPF playlist files, and publishes them via GitHub Pages. Subscribe in Parachord or any XSPF-compatible player.

## Playlists

| Station | Source | Add to Parachord | XSPF |
|---------|--------|------------------|------|
| KEXP Rewind | [kexp.org](https://www.kexp.org/playlist/) | [Add](https://parachord.com/go?uri=parachord%3A%2F%2Fimport%3Furl%3Dhttps%253A%252F%252Fjherskowitz.github.io%252Fspinbin%252Fplaylists%252Fkexp-today.xspf) | [XSPF](https://jherskowitz.github.io/spinbin/playlists/kexp-today.xspf) |
| KCRW Rewind | [kcrw.com](https://www.kcrw.com/playlists?channel=Simulcast) | [Add](https://parachord.com/go?uri=parachord%3A%2F%2Fimport%3Furl%3Dhttps%253A%252F%252Fjherskowitz.github.io%252Fspinbin%252Fplaylists%252Fkcrw-today.xspf) | [XSPF](https://jherskowitz.github.io/spinbin/playlists/kcrw-today.xspf) |
| WFMU Rewind | [wfmu.org](https://wfmu.org/playlists/) | [Add](https://parachord.com/go?uri=parachord%3A%2F%2Fimport%3Furl%3Dhttps%253A%252F%252Fjherskowitz.github.io%252Fspinbin%252Fplaylists%252Fwfmu-today.xspf) | [XSPF](https://jherskowitz.github.io/spinbin/playlists/wfmu-today.xspf) |
| WFUV Rewind | [wfuv.org](https://wfuv.org/playlist) | [Add](https://parachord.com/go?uri=parachord%3A%2F%2Fimport%3Furl%3Dhttps%253A%252F%252Fjherskowitz.github.io%252Fspinbin%252Fplaylists%252Fwfuv-today.xspf) | [XSPF](https://jherskowitz.github.io/spinbin/playlists/wfuv-today.xspf) |
| SomaFM Groove Salad Rewind | [somafm.com](https://somafm.com/groovesalad/) | [Add](https://parachord.com/go?uri=parachord%3A%2F%2Fimport%3Furl%3Dhttps%253A%252F%252Fjherskowitz.github.io%252Fspinbin%252Fplaylists%252Fsomafm-groovesalad-today.xspf) | [XSPF](https://jherskowitz.github.io/spinbin/playlists/somafm-groovesalad-today.xspf) |

## How It Works

A GitHub Actions workflow runs once a day at 5am EST, fetches playlist data from source APIs, generates XSPF files, and publishes them to GitHub Pages.

## Adding New Stations

1. Create a scraper in `scrapers/` with a `fetch_plays()` function returning `[{"title", "creator", "album", "image"}]`
2. Add an entry to `PLAYLISTS` in `generate.py`
3. Add tests, update `pages/index.html` and this README

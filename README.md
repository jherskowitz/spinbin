# Spinbin

Turning the web into playlists... one page at a time.

Spinbin scrapes radio station and chart playlists, generates XSPF playlist files, and publishes them via GitHub Pages. Subscribe in Parachord or any XSPF-compatible player.

## Playlists

| Playlist | Source | Add to Parachord | XSPF |
|----------|--------|------------------|------|
| KEXP: Today's Playlist | [kexp.org](https://www.kexp.org/playlist/) | [Add to Parachord](https://parachord.com/go?uri=parachord%3A%2F%2Fimport%3Furl%3Dhttps%253A%252F%252Fjherskowitz.github.io%252Fspinbin%252Fplaylists%252Fkexp-today.xspf) | [XSPF](https://jherskowitz.github.io/spinbin/playlists/kexp-today.xspf) |

## How It Works

A GitHub Actions workflow runs every 30 minutes, fetches playlist data from source APIs, generates XSPF files, and publishes them to GitHub Pages.

## Adding New Stations

1. Create a scraper in `scrapers/` with a `fetch_plays()` function
2. Add an entry to `PLAYLISTS` in `generate.py`
3. Add tests, update `pages/index.html` and this README

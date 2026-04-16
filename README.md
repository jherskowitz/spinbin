# Spinbin

Turning the web into playlists... one page at a time.

Spinbin scrapes radio station and chart playlists, generates XSPF playlist files, and publishes them via GitHub Pages. Subscribe in Parachord or any XSPF-compatible player.

## Playlists

| Playlist | XSPF URL | Source |
|----------|----------|--------|
| KEXP Today | `https://jherskowitz.github.io/spinbin/playlists/kexp-today.xspf` | [kexp.org](https://www.kexp.org/playlist/) |

## How It Works

A GitHub Actions workflow runs every 30 minutes, fetches playlist data from source APIs, generates XSPF files, and publishes them to GitHub Pages.

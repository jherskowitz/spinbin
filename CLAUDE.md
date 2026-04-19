# Spinbin — Claude Working Notes

Context for AI assistants (and humans new to the codebase). Start here before
making changes.

## What this is

Spinbin scrapes public radio stations' recently-played track lists, writes
them to XSPF playlist files, and publishes them via GitHub Pages. A daily
GitHub Actions cron runs `generate.py` at 5 AM EST (`0 10 * * *` UTC); the
resulting `output/` directory is pushed to `gh-pages` by
`peaceiris/actions-gh-pages`. End users subscribe to the XSPF URLs in
Parachord (or any XSPF-compatible player).

The marketing/landing page at `pages/index.html` is a static HTML site with
a client-side sort/filter JS. It's deployed alongside the XSPF files.

**Zero hosting cost** is a hard constraint. No databases, no servers — just
static files regenerated daily by CI.

## Repo layout

```
spinbin/
├── generate.py              # Orchestrator: iterates PLAYLISTS dict, writes XSPF
├── xspf.py                  # XSPF XML writer (ported from the 2014 Python 2 lib)
├── scrapers/                # One module per data source; each exports fetch_plays()
│   ├── kexp.py              # api.kexp.org/v2/plays/
│   ├── kcrw.py              # tracklist-api.kcrw.com (by date)
│   ├── wfmu.py              # RSS feed → per-show HTML scrape
│   ├── wfuv.py              # wfuv.org/playlist/feed (RSS)
│   ├── wmbr.py              # wmbr.org/dynamic.xml
│   ├── xrayfm.py            # xray.fm/playlist HTML (paginated)
│   ├── vintageobscura.py    # vintageobscura.net recent_tracks.json
│   ├── somafm.py            # somafm.com/songs/{channel}.json (parameterized!)
│   ├── spinitron.py         # Shared: scrapes data-spin="{…}" attrs (parameterized!)
│   ├── onlineradiobox.py    # Shared: /json/{country}/{slug}/playlist/{day} (parameterized!)
│   ├── radioparadise.py     # api.radioparadise.com/api/nowplaying_list
│   └── nts.py               # nts.live /api/v2/live + per-show tracklist
├── tests/                   # pytest; one file per scraper + generate + xspf
├── pages/
│   ├── index.html           # Station directory w/ sort/filter + Parachord import buttons
│   └── favicon.svg
├── .github/workflows/
│   └── generate.yml         # Daily cron → run tests → generate → deploy
└── output/                  # Build artifact; gitignored
```

## The data flow

1. `generate.py` has a `PLAYLISTS` dict keyed by station ID. Each entry:

   ```python
   "kexp": {
       "title": "KEXP Rewind",
       "creator": "kexp.org",
       "filename": "kexp-today.xspf",
       "fetch": lambda: kexp.fetch_plays(),
       "info": "https://www.kexp.org/playlist/",
   },
   ```

2. For each station, `generate_playlist()` calls `fetch()` to get a list of
   track dicts with keys `title`, `creator`, `album`, `image`. Empty feeds
   are skipped (no empty XSPF files).

3. Each track's string fields are passed through `_clean()` which
   **unescapes HTML entities** before the XML writer re-escapes — see
   "Gotcha: double-encoded `&amp;`" below.

4. `xspf.py` writes a standards-compliant `<playlist><trackList>...` file
   and returns bytes.

5. The generate step writes to `$OUTPUT_DIR/{filename}` (default
   `output/playlists/`). The workflow then copies `pages/*` into `output/`
   and deploys everything.

## Adding a new station

**If it's an existing shared scraper backend**, it's a one-line config
change. Check whether the station is on:

- **SomaFM** (`somafm.com/songs/{channel}.json`) — use `somafm.fetch_plays(channel="slug")`
- **Spinitron** (most non-commercial US stations) — use `spinitron.fetch_plays("STATION")`
- **OnlineRadioBox** (thousands of stations including SoundStack-hosted ones) — use `onlineradiobox.fetch_plays("country", "slug")`

**If it's a new backend**, create `scrapers/newstation.py`:

```python
import requests

def fetch_plays(hours=24):
    """Returns a list of {title, creator, album, image} dicts."""
    resp = requests.get("https://…/api", timeout=30,
                        headers={"User-Agent": "Spinbin/1.0 (https://github.com/jherskowitz/spinbin)"})
    resp.raise_for_status()
    data = resp.json()
    # ... transform to track dicts ...
    return tracks
```

Required conventions:
- `hours=24` keyword for the time window (can be ignored if the source doesn't expose timestamps)
- 30-second HTTP timeout (prevents runaway workflow runs)
- Descriptive `User-Agent` (SomaFM and some others block anonymous scrapers)
- Return `[]` on error — `generate.py` handles empty lists gracefully
- Track dicts with exactly `title`, `creator`, `album`, `image` keys (empty string OK)

Then:
1. Import in `generate.py` and add to `PLAYLISTS`
2. Add a test file `tests/test_newstation.py` — mock `requests.get`, verify dict shape
3. Add the station card to `pages/index.html` (copy an existing `<article class="station">`)
4. Add brand color `--newstation` to the `:root` block
5. Add `.tile--newstation { background: var(--newstation); }`
6. Tag the card with `data-name`, `data-added` (YYYY-MM-DD), `data-genre`
7. Add a row to `README.md`

## Known gotchas (read before touching)

### Double-encoded `&amp;` in track metadata

Several sources (RSS feeds, scraped HTML, some JSON APIs) deliver metadata
*pre-encoded* — `"Earth Wind &amp; Fire"` literally, not `"Earth Wind & Fire"`.
Our XML writer then escapes the `&` again, producing `&amp;amp;` in the file,
which Parachord decodes as `&amp;` on display.

**Fix** is centralized in `generate.py` via `_clean()` which calls
`html.unescape()` in a loop until stable (catches double-encoded sources).
**All scraper output goes through it — don't bypass.** Covered by
`test_generate_unescapes_html_entities_in_metadata`.

### Time-bomb tests with hardcoded dates

Several scrapers filter by a rolling 24h window based on a track's
timestamp. If tests use hardcoded dates in mock data, they pass the day
they're written and silently fail a day later in CI.

**Rule:** In any test whose scraper has time-window filtering (KEXP, KCRW,
SomaFM, Vintage Obscura, OnlineRadioBox, Radio Paradise), generate mock
dates *relative to now*:

```python
from datetime import datetime, timedelta, timezone
def _airdate(minutes_ago):
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago))\
        .strftime("%Y-%m-%dT%H:%M:%S+00:00")
```

KEXP tests blew up in CI from this once — see commits around April 17.

### Pagination quirks

- **KEXP API**: `begin_airdate` query param is honored on the first request
  but not carried through the `next` URL the API returns. If we follow
  `next` blindly, we'll runaway-paginate back to 2015. `scrapers/kexp.py`
  checks every track's airdate against the cutoff and breaks early.
  There's also a `MAX_PAGES` safety cap. Don't remove these.

- **Spinitron**: URL params like `?n=100` and `?page=2` are silently
  ignored — the page always returns ~16–30 spins. We take whatever's
  there. No paging (yet) — feature request if someone wants deeper
  history, would require scraping individual show pages.

- **XRAY.fm**: DOES support pagination at `/tracks/index/page:N?url=playlist`.
  Default `max_pages=15` yields ~300 tracks = roughly a day. Change cautiously.

- **GitHub Pages CDN caching**: After a deploy, a freshly published XSPF
  may return an OLD cached version for ~10–60 seconds. Append
  `?v=$(date +%s)` cache-buster when verifying from curl. This tripped
  me up (XRAY showed "20 tracks" when the deploy actually wrote 300 — the
  CI log always has the real number).

### Stations we **can't** currently scrape

Don't waste time re-researching these unless something has changed:

| Station | Why not |
|---|---|
| iHeartMedia stations (KIIS FM, KTU, Z100, and many others) | Their `live-meta/stream/{id}/recentlyPlayed` endpoint is 404-gated; "recently played" is only exposed to logged-in app users. API requires auth. |
| CBC Radio 3 | `services.radio-canada.ca/music/dj/v1/playbacklog` requires POST with a session token. Reverse-engineering would be fragile. |
| KKJZ (LA Jazz 88.1) | No public playlist feed discovered — not on Spinitron, not on OnlineRadioBox. |
| WWOZ | `/playlist` page only exposes the current *program* (not the track list). Track data lives in per-show HTML pages at `/programs/playlists/...`. A WFMU-style multi-show crawler would work but is time-consuming. |
| WXPN | WordPress REST API (`backend.xpn.org/wp-json/wp/v2/playlist`) has only 2 legacy "station feed" posts with null tracks. Real spin data is served from a private endpoint. |

If a user asks for one of these, mention the above and ask whether they want
a fragile workaround (e.g. browser automation) or to skip.

### NTS Radio tracklists are sparse

The `/api/v2/shows/{alias}/episodes/{episode}/tracklist` endpoint returns
tracks only if the DJ manually submitted them. Live shows often start empty
and may never get populated. Expect wildly variable daily track counts
(anywhere from 0 to ~40).

### WFMU HTML scraping is fragile but working

WFMU has no JSON API. Current approach:
1. Fetch `wfmu.org/playlistfeed.xml` (RSS of recent shows)
2. Filter items in the time window
3. For each show URL, fetch the HTML and parse its `<table id="drop_table">`

There's a specific gotcha in the HTML: each song-title `<td>` contains
a hidden `<span style="display:none" id="..._summary_html">"Song" by "Artist"</span>`
and a `<button>→</button>` for the comments UI. Naive tag-stripping
concatenates those with the visible title, producing
`'Friday I'm in Love → "Friday I'm in Love" by "The Cure"'`. The
`_strip_tags()` helper in `scrapers/wfmu.py` removes hidden spans and
buttons *first*, then strips remaining tags. Don't simplify without
replicating both removals — test case in `test_parse_show_tracks_extracts_and_filters`.

## The index page (`pages/index.html`)

Single-file HTML with inline CSS + vanilla JS. Design language mirrors
Parachord's own light-mode UI — it's not a rebellion, it's a sibling.
**Don't swap to Tailwind, a framework, or a build step** unless the project
grows beyond static hosting.

Key design tokens (pulled from `parachord-desktop/index.html`):
- Page bg: `#f6f7f9`, card bg: `#ffffff`, text: `#111827` / `#6b7280`
- Accent: `#7c3aed` (Parachord purple), hover: `#6d28d9`
- Card shadow: `0 1px 3px rgba(0,0,0,0.05), 0 4px 12px rgba(0,0,0,0.03)`
- Plugin tile: 88px rounded-square, `0 2px 8px + 0 4px 16px` shadow,
  centered 64px white logo/wordmark SVG
- System font stack (Parachord uses it; don't add webfonts)
- Border radii: sm 6, md 10, lg 16, xl 20, pill 999

### Station cards

Each `<article class="station">` carries these attrs — the sort/filter JS reads them:

```html
<article class="station"
         data-name="KEXP"
         data-added="2026-04-16"
         data-genre="indie rock eclectic public">
```

Genre taxonomy currently in use (chip filters): `indie`, `rock`,
`eclectic`, `electronic`, `ambient`, `public`, `community`, `freeform`,
`alternative`, `college`, `vintage`, `international`. When adding a new
station, reuse existing genres unless the station really warrants a new
chip. If you add a new genre, add the corresponding `<button class="chip-filter" data-genre="...">` in the chips bar.

### Sort/filter JS

Defined inline at the bottom of `index.html`. Features:
- Segmented sort toggle (Recently added / A–Z) — default is "Recently added"
- Debounced keyword search (60ms) — matches name, city, description, genre
- Single-select genre chips with "All" default
- Count badge ("N stations" / "X of N") — `aria-live="polite"`
- Empty state with reset button
- Fade-up stagger tied to JS-assigned `--order` (not nth-child), so cards
  reveal in *displayed* order even after reorder

## Parachord import protocol

Each station card has an "Add to Parachord" button with:

```
parachord://import?url={url-encoded-XSPF-URL}
```

For links that need to survive GitHub's markdown (which strips custom URL
schemes), use the web gateway at `parachord.com/go`:

```
https://parachord.com/go?uri={encoded-parachord-url}
```

The README links use the gateway; the index page's in-browser buttons use
the direct scheme (browser's registered handler dispatches to Parachord).

See the Parachord protocol schema at
`/Users/jherskowitz/Development/parachord/parachord-desktop/docs/protocol-schema.md`
for the full spec (includes inline-tracks format and security constraints).

## Shared backend scrapers — when to use which

- **Spinitron** (`spinitron.fetch_plays("STATION_CODE")`)
  - Best for: most non-commercial US college / community stations
  - Known good: WPRB, KALX, WFUV (though WFUV has its own RSS scraper)
  - Check: visit `spinitron.com/{STATION}/` — if it returns a page with
    `data-spin="{…}"` attributes, it works.
  - Limits: ~16–30 most recent spins, no deep history without show-level scraping

- **OnlineRadioBox** (`onlineradiobox.fetch_plays("country", "slug")`)
  - Best for: stations that use SoundStack, Squarespace, or other hosts
    that embed OnlineRadioBox's widget
  - Known good: Bagel Radio (`us/bagel`)
  - Check: visit `onlineradiobox.com/{country}/{slug}/` — if the page shows
    a playlist, `{country}/{slug}/playlist/0?tz=0` returns JSON
  - Limits: resolution depends on how often OnlineRadioBox polls the station

- **SomaFM** (`somafm.fetch_plays(channel="slug")`)
  - Best for: SomaFM's own channels (Groove Salad, Indie Pop Rocks, etc.)
  - Check: `somafm.com/channels.json` lists all channels with their slugs
  - Limits: ~20 most recent tracks per channel

## Commands cheat sheet

```bash
# Local dev
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v
python generate.py                     # Writes output/playlists/*.xspf

# Push + trigger a manual deploy
git push
gh workflow run generate.yml

# Watch latest workflow run
gh run watch $(gh run list --limit 1 --json databaseId --jq '.[0].databaseId') --exit-status

# Verify a deployed XSPF (with cache-buster)
curl -sL "https://jherskowitz.github.io/spinbin/playlists/STATION-today.xspf?v=$(date +%s)" | grep -c '<track>'
```

## Conventions worth keeping

- Scraper `fetch_plays()` is the *only* public function — everything else
  is `_underscore_prefixed` helpers.
- Every scraper uses `timeout=30` on requests — don't remove; the cron
  runner will hang otherwise.
- HTTP user-agent identifies Spinbin with a link to the repo (politeness +
  traceability if a station admin looks at their logs).
- Tests mock `requests.get` directly — no VCR, no live network in CI.
- Commits are small and focused, with `feat:` / `fix:` / `chore:` prefixes.
- When removing a station, drop the scraper, tests, `PLAYLISTS` entry,
  card, README row, brand color, and tile class in one commit.

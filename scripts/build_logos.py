#!/usr/bin/env python3
"""Build standalone station-logo SVGs from the index page's tile markup.

The directory page (`pages/index.html`) renders each station's tile as an
inline SVG wordmark on a CSS-styled background (`.tile--{suffix}`). We
also need *self-contained* logos to embed in XSPF feeds (and anywhere
else a station thumbnail is useful). Re-authoring those SVGs by hand
would invite drift, so this script extracts them from the page and bakes
the brand-color (or gradient) background directly into each SVG.

Run after editing the page tiles:

    python scripts/build_logos.py

Outputs `pages/logos/{playlist_key}.svg` files, one per station. The
`playlist_key` matches the keys in `generate.py`'s PLAYLISTS dict, so
each XSPF can reference its logo at:

    https://jherskowitz.github.io/spinbin/logos/{key}.svg
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "pages" / "index.html"
LOGO_DIR = ROOT / "pages" / "logos"

# Playlist key → tile-class suffix. Add a new entry here when registering
# a new station, then re-run this script.
KEY_TO_TILE = {
    "kexp": "kexp",
    "kcrw": "kcrw",
    "wfmu": "wfmu",
    "wfuv": "wfuv",
    "somafm": "somafm",
    "somafm_indiepop": "somafm-indiepop",
    "xrayfm": "xray",
    "vintageobscura": "vintage",
    "radioparadise": "rp",
    "nts": "nts",
    "wprb": "wprb",
    "kalx": "kalx",
    "wmbr": "wmbr",
    "bagelradio": "bagel",
    "siriusxmu": "siriusxmu",
}


def main():
    html = INDEX_HTML.read_text()

    color_vars = dict(
        re.findall(r"--([a-z][a-z0-9-]+):\s*(#[0-9A-Fa-f]{3,8})\s*;", html)
    )

    tiles = {
        m.group(1): m.group(2).strip().rstrip(";").strip()
        for m in re.finditer(
            r"\.tile--([a-z0-9-]+)\s*\{\s*background:\s*([^}]+?)\s*;\s*\}",
            html,
            re.DOTALL,
        )
    }

    # Extract each tile's inner SVG (allow optional HTML comment between
    # the wrapping <div> and its <svg>).
    stations = {
        m.group(1): m.group(2).strip()
        for m in re.finditer(
            r'<div class="tile tile--([a-z0-9-]+)"[^>]*>\s*'
            r"(?:<!--[^-]*-->\s*)?"
            r'<svg[^>]*viewBox="0 0 64 64"[^>]*>(.*?)</svg>',
            html,
            re.DOTALL,
        )
    }

    LOGO_DIR.mkdir(exist_ok=True)
    written = []
    missing = []
    for key, tile_suffix in KEY_TO_TILE.items():
        inner = stations.get(tile_suffix)
        bg = tiles.get(tile_suffix)
        if not inner or not bg:
            missing.append(f"{key} ({tile_suffix})")
            continue
        defs, fill = _build_background(bg, color_vars)
        svg = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" '
            'width="256" height="256" role="img" aria-label="Spinbin station logo">\n'
            f"  {defs}\n"
            f'  <rect width="64" height="64" rx="14" ry="14" fill="{fill}"/>\n'
            f"  {inner}\n"
            "</svg>\n"
        )
        (LOGO_DIR / f"{key}.svg").write_text(svg)
        written.append(key)

    print(f"Wrote {len(written)} logos to {LOGO_DIR.relative_to(ROOT)}/")
    for k in written:
        print(f"  ✓ {k}.svg")
    if missing:
        print("\nMissing (check tile markup or KEY_TO_TILE map):")
        for m in missing:
            print(f"  ✗ {m}")
        sys.exit(1)


def _resolve_color(token, color_vars):
    token = token.strip()
    m = re.fullmatch(r"var\(--([a-z0-9-]+)\)", token)
    if m:
        return color_vars.get(m.group(1), "#000000")
    return token


def _build_background(bg_css, color_vars):
    """Return (defs_xml, fill) from a CSS background value."""
    bg_css = bg_css.strip()

    if bg_css.startswith("var("):
        return "", _resolve_color(bg_css, color_vars)
    if bg_css.startswith("#"):
        return "", bg_css

    # linear-gradient(180deg, A 0%, B 100%)
    m = re.match(
        r"linear-gradient\(\s*(\d+deg|to[^,]+),\s*(.+?)\s*\)", bg_css, re.DOTALL
    )
    if m:
        direction, stops_str = m.group(1), m.group(2)
        stops = _parse_stops(stops_str, color_vars)
        x1, y1, x2, y2 = "0%", "0%", "0%", "100%"  # 180deg default
        if "0deg" in direction or "to top" in direction:
            x1, y1, x2, y2 = "0%", "100%", "0%", "0%"
        elif "90deg" in direction or "to right" in direction:
            x1, y1, x2, y2 = "0%", "0%", "100%", "0%"
        defs = (
            f'<defs><linearGradient id="g" '
            f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
        )
        for color, pos in stops:
            defs += f'<stop offset="{pos}" stop-color="{color}"/>'
        defs += "</linearGradient></defs>"
        return defs, "url(#g)"

    # radial-gradient(circle at X% Y%, A 0%, B 55%, C 100%)
    m = re.match(
        r"radial-gradient\(\s*circle\s+at\s+(\d+)%\s+(\d+)%,\s*(.+?)\s*\)",
        bg_css,
        re.DOTALL,
    )
    if m:
        cx, cy, stops_str = m.group(1), m.group(2), m.group(3)
        stops = _parse_stops(stops_str, color_vars)
        defs = f'<defs><radialGradient id="g" cx="{cx}%" cy="{cy}%" r="75%">'
        for color, pos in stops:
            defs += f'<stop offset="{pos}" stop-color="{color}"/>'
        defs += "</radialGradient></defs>"
        return defs, "url(#g)"

    return "", "#000000"


def _parse_stops(stops_str, color_vars):
    stops = []
    for s in re.split(r",(?![^()]*\))", stops_str):
        sm = re.match(r"(\S+)\s+(\d+%)", s.strip())
        if sm:
            stops.append((_resolve_color(sm.group(1), color_vars), sm.group(2)))
    return stops


if __name__ == "__main__":
    main()

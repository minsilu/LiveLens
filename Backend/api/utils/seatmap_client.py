"""
Ticketmaster seatmap utilities.

Public API:
    get_seatmap_data(venue_name, section) -> SeatmapData | None
"""

import json
import logging
import os
import re
from typing import Optional

import httpx
from sqlalchemy import text

logger = logging.getLogger(__name__)

# TM PNG images are 1024 × 768; SVG viewBox is 10240 × 7680
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 768
SVG_SCALE = 10

_TM_HEADERS = {"User-Agent": "LiveLens/1.0"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(venue_name: str) -> str:
    """'Madison Square Garden' -> 'madison_square_garden'"""
    return re.sub(r"[^a-z0-9]+", "_", venue_name.lower()).strip("_")


def _get_engine():
    from ..database import engine  # lazy to avoid circular import
    return engine


# ---------------------------------------------------------------------------
# DB cache – SeatmapCache (per-venue: png_url + section coords)
# ---------------------------------------------------------------------------

def _cache_get(venue_key: str) -> Optional[dict]:
    engine = _get_engine()
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT png_url, section_coords FROM SeatmapCache WHERE id = :key"),
                {"key": venue_key},
            ).fetchone()
        if row and row[0]:
            coords = json.loads(row[1]) if row[1] else {}
            return {"png_url": row[0], "section_coords": coords}
    except Exception as e:
        logger.warning("SeatmapCache read error: %s", e)
    return None


def _cache_set(venue_key: str, tm_venue_id: Optional[str], png_url: Optional[str], section_coords: dict) -> None:
    engine = _get_engine()
    if not engine:
        return
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO SeatmapCache (id, tm_venue_id, png_url, section_coords) "
                    "VALUES (:id, :tm_venue_id, :png_url, :section_coords) "
                    "ON CONFLICT (id) DO UPDATE SET "
                    "tm_venue_id = EXCLUDED.tm_venue_id, "
                    "png_url = EXCLUDED.png_url, "
                    "section_coords = EXCLUDED.section_coords"
                ),
                {
                    "id": venue_key,
                    "tm_venue_id": tm_venue_id,
                    "png_url": png_url,
                    "section_coords": json.dumps(section_coords),
                },
            )
        logger.info("SeatmapCache stored: %s (%d sections)", venue_key, len(section_coords))
    except Exception as e:
        logger.warning("SeatmapCache write error: %s", e)


# ---------------------------------------------------------------------------
# Ticketmaster Discovery API
# ---------------------------------------------------------------------------

def _fetch_tm_urls(venue_name: str):
    """Return (venue_id, png_url, svg_url) from TM, or (None, None, None) on failure."""
    api_key = os.environ.get("TICKETMASTER_API_KEY")
    if not api_key:
        logger.error("TICKETMASTER_API_KEY not set")
        return None, None, None

    try:
        r = httpx.get(
            "https://app.ticketmaster.com/discovery/v2/venues.json",
            params={"keyword": venue_name, "apikey": api_key, "size": 1},
            headers=_TM_HEADERS,
            timeout=10,
        )
        venues = r.json().get("_embedded", {}).get("venues", [])
        if not venues:
            return None, None, None
        venue_id = venues[0]["id"]

        r2 = httpx.get(
            "https://app.ticketmaster.com/discovery/v2/events.json",
            params={"venueId": venue_id, "apikey": api_key, "size": 1},
            headers=_TM_HEADERS,
            timeout=10,
        )
        events = r2.json().get("_embedded", {}).get("events", [])
        if not events:
            return venue_id, None, None

        png_url = events[0].get("seatmap", {}).get("staticUrl")
        if not png_url:
            return venue_id, None, None

        svg_url = png_url.replace("type=png", "type=svg")
        return venue_id, png_url, svg_url

    except Exception as e:
        logger.error("TM API error: %s", e)
        return None, None, None


# ---------------------------------------------------------------------------
# SVG section coordinate extraction
# ---------------------------------------------------------------------------

def _extract_section_coords(svg_content: str) -> dict:
    """
    Parse a TM seatmap SVG and return every section's center pixel on the
    1024×768 PNG (SVG coords divided by SVG_SCALE=10).

    Returns: {"101": [x, y], "Floor": [x, y], ...}
    """
    results = {}

    def _centroid(d_value: str):
        nums = [float(n) for n in re.findall(r"[-+]?\d+\.?\d*", d_value)]
        pts = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
        if not pts:
            return None
        cx = int(sum(p[0] for p in pts) / len(pts) / SVG_SCALE)
        cy = int(sum(p[1] for p in pts) / len(pts) / SVG_SCALE)
        return [cx, cy]

    # <path id="..." d="..."> (both attribute orderings)
    for m in re.finditer(r'<path\s[^>]*?id="([^"]+)"[^>]*?d="([^"]+)"[^>]*/>', svg_content):
        c = _centroid(m.group(2))
        if c:
            results[m.group(1)] = c

    for m in re.finditer(r'<path\s[^>]*?d="([^"]+)"[^>]*?id="([^"]+)"[^>]*/>', svg_content):
        if m.group(2) not in results:
            c = _centroid(m.group(1))
            if c:
                results[m.group(2)] = c

    # <text x="..." y="...">label</text>
    for m in re.finditer(r'<text[^>]*x="([^"]+)"[^>]*y="([^"]+)"[^>]*>\s*([^<]+?)\s*</text>', svg_content):
        label = m.group(3).strip()
        if label and label not in results:
            try:
                results[label] = [
                    int(float(m.group(1)) / SVG_SCALE),
                    int(float(m.group(2)) / SVG_SCALE),
                ]
            except ValueError:
                pass

    logger.info("Extracted %d section coords from SVG", len(results))
    return results


# ---------------------------------------------------------------------------
# Seatmap fetch + cache
# ---------------------------------------------------------------------------

def _fetch_and_cache(venue_name: str) -> Optional[dict]:
    venue_key = _normalize(venue_name)
    venue_id, png_url, svg_url = _fetch_tm_urls(venue_name)

    if not png_url or not svg_url:
        _cache_set(venue_key, venue_id, None, {})
        return None

    try:
        svg = httpx.get(svg_url, timeout=15, headers=_TM_HEADERS).text
        coords = _extract_section_coords(svg)
        _cache_set(venue_key, venue_id, png_url, coords)
        return {"png_url": png_url, "section_coords": coords}
    except Exception as e:
        logger.error("Failed to fetch/cache seatmap for %s: %s", venue_name, e)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_seatmap_data(venue_name: str, section: str) -> Optional[dict]:
    """
    Return seatmap metadata for the given venue + section.

    Result:
        {
            "image_url": str,        # TM PNG URL (1024×768)
            "pin_x":     int | None, # pixel x on the PNG, or None if section unknown
            "pin_y":     int | None, # pixel y on the PNG, or None if section unknown
        }

    Returns None if no seatmap is available for this venue.
    """
    venue_key = _normalize(venue_name)

    seatmap = _cache_get(venue_key)
    if seatmap is None:
        seatmap = _fetch_and_cache(venue_name)

    if not seatmap:
        return None

    coord = seatmap["section_coords"].get(section)
    return {
        "image_url": seatmap["png_url"],
        "pin_x": coord[0] if coord else None,
        "pin_y": coord[1] if coord else None,
    }

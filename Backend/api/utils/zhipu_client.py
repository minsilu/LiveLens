import os
import io
import re
import json
import logging
import httpx
import boto3
from botocore.config import Config
from typing import List, Optional, Dict, Tuple
from sqlalchemy import text

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = None

try:
    from zhipuai import ZhipuAI
except ImportError:
    ZhipuAI = None

logger = logging.getLogger(__name__)

# We will initialize the client lazily inside the function 
# to ensure load_dotenv() has already populated os.environ.
_client = None

def get_client():
    global _client
    if _client is None:
        if ZhipuAI is None:
            print("ZhipuAI package is not installed.")
            return None
        
        api_key = os.environ.get("ZHIPUAI_API_KEY")
        if not api_key:
            print("ERROR: ZHIPUAI_API_KEY environment variable is missing!")
            return None
            
        try:
            _client = ZhipuAI(api_key=api_key)
        except Exception as e:
            print(f"Failed to initialize ZhipuAI client: {e}")
            return None
    return _client

def extract_tags(review_text: str) -> List[str]:
    """
    Extracts 1 to 5 concise tags from the given review text using Zhipu AI.
    """
    client = get_client()
    if not client:
        return []

    if not review_text or not review_text.strip():
        return []

    prompt = (
        "You are an AI assistant for a live event review platform. "
        "Your task is to analyze the following review text and extract 1 to 5 highly relevant, "
        "concise tags (1-3 words each) that summarize the key aspects of the user's experience "
        "(e.g., 'Great View', 'Loud Sound', 'Expensive', 'Friendly Staff', 'Comfortable Seats').\n\n"
        "Return ONLY a valid JSON array of strings containing the tags, and nothing else. "
        "Example output: [\"Great View\", \"Loud Sound\"]\n\n"
        f"Review text:\n{review_text}"
    )

    try:
        print(f"DEBUG: Starting ZhipuAI request (review length: {len(review_text)} characters)...")
        response = client.chat.completions.create(
            model="glm-4",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            timeout=60, # Increased timeout for cloud environment
        )
        print("DEBUG: ZhipuAI response received.")
        
        # Extract the content from the response
        content = response.choices[0].message.content
        
        # Clean the response in case the model adds markdown formatting (e.g. ```json ... ```)
        content = content.replace("```json", "").replace("```", "").strip()
        
        # Parse the JSON string into a Python list
        try:
            tags = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"DEBUG: Failed to parse AI response as JSON. Content: {content}")
            return []
        
        if isinstance(tags, list):
            # Limit to max 5 tags just in case
            return tags[:5]
        else:
             print(f"DEBUG: ZhipuAI returned non-list format: {content}")
             return []
             
    except Exception as e:
        print(f"CRITICAL: extract_tags failed. Error type: {type(e).__name__}, Message: {str(e)}")
        import traceback
        traceback.print_exc()
        return []


# ── Seatmap pinning helpers ──────────────────────────────────────────────────

_TM_HEADERS = {"User-Agent": "LiveLens/1.0"}


def _normalize(venue_name: str) -> str:
    """Normalize venue name into a safe, lowercase, underscore-separated key."""
    return re.sub(r"[^a-z0-9]", "_", venue_name.lower()).strip("_")


def _get_engine():
    """Lazy import to avoid circular dependency with database module."""
    from ..database import engine
    return engine


# ── Tier 1: Per-section pinned-image cache ───────────────────────────────────

def _lookup_pin_cache(pin_key: str) -> Optional[str]:
    """Check SeatmapPinCache for an already-rendered S3 URL."""
    engine = _get_engine()
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT s3_url FROM SeatmapPinCache WHERE id = :key"),
                {"key": pin_key},
            ).fetchone()
            if row:
                logger.info(f"Pin cache HIT: {pin_key}")
                return row[0]
    except Exception as e:
        logger.warning(f"Pin cache lookup failed: {e}")
    return None


def _store_pin_cache(pin_key: str, venue_key: str, section: str, s3_url: str) -> None:
    """Store a rendered pinned-image URL in SeatmapPinCache."""
    engine = _get_engine()
    if not engine:
        return
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO SeatmapPinCache (id, venue_key, section, s3_url) "
                    "VALUES (:id, :venue_key, :section, :s3_url) "
                    "ON CONFLICT (id) DO UPDATE SET s3_url = :s3_url"
                ),
                {"id": pin_key, "venue_key": venue_key, "section": section, "s3_url": s3_url},
            )
        logger.info(f"Pin cache STORED: {pin_key}")
    except Exception as e:
        logger.warning(f"Pin cache store failed: {e}")


# ── Tier 2: Per-venue seatmap metadata + coordinates cache ───────────────────

def _lookup_seatmap_cache(venue_key: str) -> Optional[dict]:
    """Look up cached Ticketmaster metadata and section coordinates for a venue."""
    engine = _get_engine()
    if not engine:
        return None
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT tm_venue_id, png_url, section_coords FROM SeatmapCache WHERE id = :key"),
                {"key": venue_key},
            ).fetchone()
            if row:
                logger.info(f"Seatmap cache HIT: {venue_key}")
                coords = {}
                if row[2]:
                    try:
                        coords = json.loads(row[2])
                    except json.JSONDecodeError:
                        pass
                return {
                    "tm_venue_id": row[0],
                    "png_url": row[1],
                    "section_coords": coords,
                }
    except Exception as e:
        logger.warning(f"Seatmap cache lookup failed: {e}")
    return None


def _store_seatmap_cache(
    venue_key: str,
    tm_venue_id: Optional[str],
    png_url: Optional[str],
    section_coords: Dict[str, Tuple[int, int]],
) -> None:
    """Store venue-level seatmap metadata in SeatmapCache."""
    engine = _get_engine()
    if not engine:
        return
    try:
        coords_json = json.dumps(section_coords)
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO SeatmapCache (id, tm_venue_id, png_url, section_coords) "
                    "VALUES (:id, :tm_venue_id, :png_url, :section_coords) "
                    "ON CONFLICT (id) DO UPDATE SET "
                    "tm_venue_id = :tm_venue_id, png_url = :png_url, section_coords = :section_coords"
                ),
                {
                    "id": venue_key,
                    "tm_venue_id": tm_venue_id,
                    "png_url": png_url,
                    "section_coords": coords_json,
                },
            )
        logger.info(f"Seatmap cache STORED: {venue_key} ({len(section_coords)} sections)")
    except Exception as e:
        logger.warning(f"Seatmap cache store failed: {e}")


# ── Ticketmaster API helpers ─────────────────────────────────────────────────

def _get_tm_seatmap_urls(venue_name: str):
    """Fetch Ticketmaster venue_id, PNG seatmap URL and SVG seatmap URL for a venue."""
    tm_key = os.environ.get("TICKETMASTER_API_KEY")
    if not tm_key:
        return None, None, None
    try:
        # 1. Find venue
        r = httpx.get(
            "https://app.ticketmaster.com/discovery/v2/venues.json",
            params={"keyword": venue_name, "apikey": tm_key, "size": 1},
            headers=_TM_HEADERS,
            timeout=10,
        )
        venues = r.json().get("_embedded", {}).get("venues", [])
        if not venues:
            return None, None, None
        venue_id = venues[0]["id"]

        # 2. Get an upcoming event for that venue
        r2 = httpx.get(
            "https://app.ticketmaster.com/discovery/v2/events.json",
            params={"venueId": venue_id, "apikey": tm_key, "size": 1},
            headers=_TM_HEADERS,
            timeout=10,
        )
        events = r2.json().get("_embedded", {}).get("events", [])
        if not events:
            return venue_id, None, None
        # Get seatmap URL from event response (contains the correct internal event ID)
        png_url = events[0].get("seatmap", {}).get("staticUrl")
        if not png_url:
            return venue_id, None, None
        # Derive SVG URL from PNG URL by replacing type=png with type=svg
        svg_url = png_url.replace("type=png", "type=svg")
        return venue_id, png_url, svg_url
    except Exception as e:
        logger.error(f"TM seatmap lookup failed: {e}")
        return None, None, None


# ── SVG coordinate extraction ────────────────────────────────────────────────

def _get_section_center(svg_content: str, section: str):
    """Parse SVG and return (px_x, px_y) center of the given section. SVG viewBox is 10240x7680, image 1024x768."""
    SCALE = 10

    # Strategy 1: path with id="<section>"
    path_match = re.search(rf'<path[^>]*id="{re.escape(section)}"[^>]*/>', svg_content)
    if path_match:
        d_match = re.search(r'd="([^"]+)"', path_match.group(0))
        if d_match:
            nums = [float(n) for n in re.findall(r'[-+]?\d+\.?\d*', d_match.group(1))]
            coords = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
            if coords:
                return (
                    int(sum(c[0] for c in coords) / len(coords) / SCALE),
                    int(sum(c[1] for c in coords) / len(coords) / SCALE),
                )

    # Strategy 2: text element containing the section label
    text_match = re.search(
        rf'<text[^>]*x="([^"]+)"[^>]*y="([^"]+)"[^>]*>\s*{re.escape(section)}\s*</text>',
        svg_content,
    )
    if text_match:
        x = int(float(text_match.group(1)) / SCALE)
        y = int(float(text_match.group(2)) / SCALE)
        return x, y

    return None


def _extract_all_section_coords(svg_content: str) -> Dict[str, Tuple[int, int]]:
    """
    Parse SVG once and extract center coordinates for ALL sections found.
    Returns a dict like {"101": (512, 256), "102": (340, 180), ...}
    """
    SCALE = 10
    results: Dict[str, Tuple[int, int]] = {}

    # Strategy 1: Find all <path> elements with an id attribute
    for match in re.finditer(r'<path\s[^>]*?id="([^"]+)"[^>]*?d="([^"]+)"[^>]*/>', svg_content):
        section_id = match.group(1)
        d_value = match.group(2)
        nums = [float(n) for n in re.findall(r'[-+]?\d+\.?\d*', d_value)]
        coords = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
        if coords:
            cx = int(sum(c[0] for c in coords) / len(coords) / SCALE)
            cy = int(sum(c[1] for c in coords) / len(coords) / SCALE)
            results[section_id] = (cx, cy)

    # Also try d before id order
    for match in re.finditer(r'<path\s[^>]*?d="([^"]+)"[^>]*?id="([^"]+)"[^>]*/>', svg_content):
        d_value = match.group(1)
        section_id = match.group(2)
        if section_id not in results:
            nums = [float(n) for n in re.findall(r'[-+]?\d+\.?\d*', d_value)]
            coords = [(nums[i], nums[i + 1]) for i in range(0, len(nums) - 1, 2)]
            if coords:
                cx = int(sum(c[0] for c in coords) / len(coords) / SCALE)
                cy = int(sum(c[1] for c in coords) / len(coords) / SCALE)
                results[section_id] = (cx, cy)

    # Strategy 2: Find <text> elements with x/y attributes and section labels
    for match in re.finditer(
        r'<text[^>]*x="([^"]+)"[^>]*y="([^"]+)"[^>]*>\s*([^<]+?)\s*</text>',
        svg_content,
    ):
        x_str, y_str, label = match.group(1), match.group(2), match.group(3).strip()
        if label and label not in results:
            try:
                cx = int(float(x_str) / SCALE)
                cy = int(float(y_str) / SCALE)
                results[label] = (cx, cy)
            except (ValueError, ZeroDivisionError):
                continue

    logger.info(f"Extracted {len(results)} section coordinates from SVG")
    return results


# ── S3 upload ────────────────────────────────────────────────────────────────

def _upload_to_s3(img_bytes: bytes, s3_key: str) -> Optional[str]:
    """Upload PNG bytes to S3 and return public URL."""
    bucket = os.environ.get("S3_BUCKET_NAME", "livelens-images")
    region = os.environ.get("AWS_REGION", "us-east-2")
    try:
        s3 = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.environ.get("AWS_SESSION_TOKEN"),
            config=Config(s3={"addressing_style": "virtual"}, signature_version="s3v4"),
        )
        s3.put_object(
            Bucket=bucket,
            Key=s3_key,
            Body=img_bytes,
            ContentType="image/png",
        )
        return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
    except Exception as e:
        logger.error(f"S3 upload failed: {e}")
        return None


# ── Seatmap fetch + cache orchestrator ───────────────────────────────────────

def _fetch_and_cache_seatmap(venue_name: str) -> Optional[dict]:
    """
    Hit Ticketmaster APIs, download SVG, extract ALL section coordinates,
    and store everything in SeatmapCache. Returns the cached dict or None.
    """
    venue_key = _normalize(venue_name)
    tm_venue_id, png_url, svg_url = _get_tm_seatmap_urls(venue_name)

    if not png_url or not svg_url:
        # Store a "miss" record so we don't retry TM for this venue
        _store_seatmap_cache(venue_key, tm_venue_id, None, {})
        return {"tm_venue_id": tm_venue_id, "png_url": None, "section_coords": {}}

    try:
        svg_content = httpx.get(svg_url, timeout=15, headers=_TM_HEADERS).text
        section_coords = _extract_all_section_coords(svg_content)

        # Convert tuples to lists for JSON serialization
        coords_serializable = {k: list(v) for k, v in section_coords.items()}
        _store_seatmap_cache(venue_key, tm_venue_id, png_url, coords_serializable)

        return {
            "tm_venue_id": tm_venue_id,
            "png_url": png_url,
            "section_coords": coords_serializable,
        }
    except Exception as e:
        logger.error(f"Failed to fetch/cache seatmap for {venue_name}: {e}")
        return None


# ── PIL pin rendering ────────────────────────────────────────────────────────

def _render_pin_on_seatmap(png_url: str, x: int, y: int) -> Optional[bytes]:
    """Download PNG seatmap and draw a pin marker at (x, y). Returns PNG bytes."""
    if Image is None:
        return None
    try:
        png_bytes = httpx.get(png_url, timeout=15, headers=_TM_HEADERS).content
        img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
        draw = ImageDraw.Draw(img)
        # Outer glow
        draw.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(220, 38, 38, 80))
        # Red circle
        draw.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(220, 38, 38, 230))
        # White center dot
        draw.ellipse([x - 6, y - 6, x + 6, y + 6], fill=(255, 255, 255, 255))

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception as e:
        logger.error(f"PIL pin rendering failed: {e}")
        return None



# ── Main entry point (two-tier cached) ───────────────────────────────────────

def generate_seat_view_image(
    venue_name: str,
    section: str,
    row: str,
    seat_number: str,
) -> Optional[str]:
    """
    Generate a seatmap image with a pin on the given section.

    Uses a two-tier cache strategy:
      Tier 1 — SeatmapPinCache: check if the final pinned image already exists on S3.
      Tier 2 — SeatmapCache: check if we have pre-extracted SVG coordinates for this venue.
               If so, only download the PNG, draw pin, upload, and cache the result.

    Returns a public image URL on success, or None if the venue/section is not available.
    """
    venue_key = _normalize(venue_name)
    pin_key = f"{venue_key}_sec{section}"

    # ── Tier 1: Do we already have the final pinned image? ──
    cached_url = _lookup_pin_cache(pin_key)
    if cached_url:
        return cached_url

    # ── Tier 2: Do we have seatmap metadata for this venue? ──
    seatmap = _lookup_seatmap_cache(venue_key)
    if not seatmap:
        seatmap = _fetch_and_cache_seatmap(venue_name)

    if seatmap and seatmap.get("png_url"):
        coords = seatmap.get("section_coords", {})
        coord = coords.get(section)
        if coord:
            x, y = coord[0], coord[1]
            img_bytes = _render_pin_on_seatmap(seatmap["png_url"], x, y)
            if img_bytes:
                s3_key = f"seatmaps/{venue_key}_sec{section}.png"
                s3_url = _upload_to_s3(img_bytes, s3_key)
                if s3_url:
                    _store_pin_cache(pin_key, venue_key, section, s3_url)
                    logger.info(f"Pinned seatmap uploaded and cached: {s3_url}")
                    return s3_url

    logger.info(f"Seatmap pin not available for {venue_name} section {section}")
    return None

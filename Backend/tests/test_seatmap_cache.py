"""
Tests for the optimized seatmap pinning cache in zhipu_client.py.

Covers:
 - _normalize() helper
 - _extract_all_section_coords() with sample SVG data
 - Two-tier cache flow (pin cache hit, seatmap cache hit, full miss)
"""

import json
import pytest
from unittest.mock import patch, MagicMock

# We need to be able to import the module under test.
# Since it uses relative imports, we patch around that.
import sys
import os

# Add Backend to the Python path so we can import the api package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestNormalize:
    """Tests for the _normalize() venue name helper."""

    def test_basic_lowercase(self):
        from api.utils.zhipu_client import _normalize
        assert _normalize("Madison Square Garden") == "madison_square_garden"

    def test_special_characters(self):
        from api.utils.zhipu_client import _normalize
        assert _normalize("Scotiabank Arena (Toronto)") == "scotiabank_arena__toronto"

    def test_already_clean(self):
        from api.utils.zhipu_client import _normalize
        assert _normalize("msg") == "msg"

    def test_numbers(self):
        from api.utils.zhipu_client import _normalize
        assert _normalize("Arena 305") == "arena_305"


class TestExtractAllSectionCoords:
    """Tests for _extract_all_section_coords() with synthetic SVG content."""

    SAMPLE_SVG_PATHS = """
    <svg viewBox="0 0 10240 7680">
      <path id="101" d="M 5120 3840 L 5632 3840 L 5632 4352 L 5120 4352 Z" />
      <path id="202" d="M 2560 1920 L 3072 1920 L 3072 2432 L 2560 2432 Z" />
    </svg>
    """

    SAMPLE_SVG_TEXT = """
    <svg viewBox="0 0 10240 7680">
      <text x="5120" y="3840">FLOOR</text>
      <text x="2560" y="1920">BALCONY</text>
    </svg>
    """

    SAMPLE_SVG_MIXED = """
    <svg viewBox="0 0 10240 7680">
      <path id="101" d="M 5120 3840 L 5632 3840 L 5632 4352 L 5120 4352 Z" />
      <text x="2560" y="1920">BALCONY</text>
    </svg>
    """

    def test_extracts_from_paths(self):
        from api.utils.zhipu_client import _extract_all_section_coords
        coords = _extract_all_section_coords(self.SAMPLE_SVG_PATHS)
        assert "101" in coords
        assert "202" in coords
        # Section 101: avg of (5120,3840), (5632,3840), (5632,4352), (5120,4352)
        # = (5376, 4096) / 10 = (537, 409)
        assert coords["101"] == (537, 409)
        # Section 202: avg of (2560,1920), (3072,1920), (3072,2432), (2560,2432)
        # = (2816, 2176) / 10 = (281, 217)
        assert coords["202"] == (281, 217)

    def test_extracts_from_text_elements(self):
        from api.utils.zhipu_client import _extract_all_section_coords
        coords = _extract_all_section_coords(self.SAMPLE_SVG_TEXT)
        assert "FLOOR" in coords
        assert coords["FLOOR"] == (512, 384)
        assert "BALCONY" in coords
        assert coords["BALCONY"] == (256, 192)

    def test_mixed_path_and_text(self):
        from api.utils.zhipu_client import _extract_all_section_coords
        coords = _extract_all_section_coords(self.SAMPLE_SVG_MIXED)
        assert "101" in coords
        assert "BALCONY" in coords

    def test_empty_svg(self):
        from api.utils.zhipu_client import _extract_all_section_coords
        coords = _extract_all_section_coords("<svg></svg>")
        assert coords == {}

    def test_returns_dict(self):
        from api.utils.zhipu_client import _extract_all_section_coords
        coords = _extract_all_section_coords(self.SAMPLE_SVG_PATHS)
        assert isinstance(coords, dict)
        for key, val in coords.items():
            assert isinstance(key, str)
            assert isinstance(val, tuple)
            assert len(val) == 2


class TestTwoTierCacheFlow:
    """Integration tests for the generate_seat_view_image two-tier cache."""

    @patch("api.utils.zhipu_client._lookup_pin_cache")
    def test_tier1_cache_hit_returns_immediately(self, mock_pin_cache):
        """When SeatmapPinCache has the URL, no other work should be done."""
        from api.utils.zhipu_client import generate_seat_view_image
        mock_pin_cache.return_value = "https://s3.example.com/cached.png"

        result = generate_seat_view_image("MSG", "101", "A", "1")

        assert result == "https://s3.example.com/cached.png"
        mock_pin_cache.assert_called_once()

    @patch("api.utils.zhipu_client._store_pin_cache")
    @patch("api.utils.zhipu_client._upload_to_s3")
    @patch("api.utils.zhipu_client._render_pin_on_seatmap")
    @patch("api.utils.zhipu_client._lookup_seatmap_cache")
    @patch("api.utils.zhipu_client._lookup_pin_cache")
    def test_tier2_cache_hit_renders_and_caches(
        self, mock_pin_cache, mock_seatmap_cache, mock_render, mock_s3, mock_store_pin
    ):
        """When SeatmapPinCache misses but SeatmapCache has coords, render + cache."""
        from api.utils.zhipu_client import generate_seat_view_image

        mock_pin_cache.return_value = None  # Tier 1 miss
        mock_seatmap_cache.return_value = {
            "tm_venue_id": "KovZ12345",
            "png_url": "https://mapsapi.tmol.io/maps/geometry/3/event/123/staticImage?type=png",
            "section_coords": {"101": [512, 256]},
        }
        mock_render.return_value = b"fake_png_bytes"
        mock_s3.return_value = "https://livelens-images.s3.us-east-2.amazonaws.com/seatmaps/msg_sec101.png"

        result = generate_seat_view_image("MSG", "101", "A", "1")

        assert result == "https://livelens-images.s3.us-east-2.amazonaws.com/seatmaps/msg_sec101.png"
        mock_render.assert_called_once()
        mock_s3.assert_called_once()
        mock_store_pin.assert_called_once()

    @patch("api.utils.zhipu_client._fetch_and_cache_seatmap")
    @patch("api.utils.zhipu_client._lookup_seatmap_cache")
    @patch("api.utils.zhipu_client._lookup_pin_cache")
    def test_full_miss_returns_none(
        self, mock_pin_cache, mock_seatmap_cache, mock_fetch
    ):
        """When both caches miss and TM has no data, return None (no AI fallback)."""
        from api.utils.zhipu_client import generate_seat_view_image

        mock_pin_cache.return_value = None
        mock_seatmap_cache.return_value = None
        mock_fetch.return_value = {"tm_venue_id": None, "png_url": None, "section_coords": {}}

        result = generate_seat_view_image("Unknown Venue", "X", "1", "1")

        assert result is None

    @patch("api.utils.zhipu_client._lookup_seatmap_cache")
    @patch("api.utils.zhipu_client._lookup_pin_cache")
    def test_section_not_in_coords_returns_none(
        self, mock_pin_cache, mock_seatmap_cache
    ):
        """When the venue coords exist but this specific section isn't found, return None."""
        from api.utils.zhipu_client import generate_seat_view_image

        mock_pin_cache.return_value = None
        mock_seatmap_cache.return_value = {
            "tm_venue_id": "KovZ12345",
            "png_url": "https://example.com/map.png",
            "section_coords": {"101": [512, 256]},  # section 999 not present
        }

        result = generate_seat_view_image("MSG", "999", "A", "1")

        assert result is None

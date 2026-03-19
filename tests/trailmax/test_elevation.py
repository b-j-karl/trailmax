"""Tests for trailmax.elevation module."""

import pytest

from trailmax.elevation import (
    LinzElevationProvider,
    _parse_raster_elevation,
)


class TestLinzElevationProviderInit:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("LINZ_API_KEY", raising=False)

        with pytest.raises(ValueError, match="LINZ API key is required"):
            LinzElevationProvider()

    def test_accepts_explicit_api_key(self):
        provider = LinzElevationProvider(api_key="test-key-123")

        assert provider._api_key == "test-key-123"  # noqa: SLF001

    def test_reads_env_var(self, monkeypatch):
        monkeypatch.setenv("LINZ_API_KEY", "env-key-456")

        provider = LinzElevationProvider()

        assert provider._api_key == "env-key-456"  # noqa: SLF001


class TestParseRasterElevation:
    def test_extracts_band_value(self):
        data = {
            "rasterQuery": {
                "layers": {
                    "121859": {
                        "bands": [{"value": 42.5}],
                    },
                },
            },
        }

        assert _parse_raster_elevation(data, 121859) == 42.5

    def test_missing_layer_returns_zero(self):
        data = {"rasterQuery": {"layers": {}}}

        assert _parse_raster_elevation(data, 121859) == 0.0

    def test_null_value_returns_zero(self):
        data = {
            "rasterQuery": {
                "layers": {
                    "121859": {
                        "bands": [{"value": None}],
                    },
                },
            },
        }

        assert _parse_raster_elevation(data, 121859) == 0.0

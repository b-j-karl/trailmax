"""Elevation providers for TrailMax route optimisation."""

import logging
import os
from abc import ABC, abstractmethod

import networkx as nx
import requests

logger = logging.getLogger(__name__)

_LINZ_LAYER_ID = 121859
_LINZ_BASE_URL = "https://data.linz.govt.nz/services/query/v1/raster.json"
_LINZ_TIMEOUT_S = 10


class ElevationProvider(ABC):
    """Abstract base class for elevation data providers."""

    @abstractmethod
    def get_elevation(self, lat: float, lon: float) -> float:
        """Return the elevation in metres for a given coordinate.

        Args:
            lat: Latitude in decimal degrees.
            lon: Longitude in decimal degrees.

        Returns:
            Elevation above sea level in metres.
        """


class MockElevationProvider(ElevationProvider):
    """Stub elevation provider that always returns zero metres.

    Useful for testing and as a placeholder until a real NZ
    elevation source is integrated.
    """

    def get_elevation(self, lat: float, lon: float) -> float:  # noqa: ARG002
        """Return a mock elevation of 0 m for any coordinate.

        Args:
            lat: Latitude in decimal degrees (unused).
            lon: Longitude in decimal degrees (unused).

        Returns:
            Always 0.0.
        """
        return 0.0


class LinzElevationProvider(ElevationProvider):
    """Elevation provider using the LINZ NZ LiDAR 1 m DEM raster query API.

    Queries the Koordinates spatial-query-grid endpoint hosted on
    ``data.linz.govt.nz`` for layer 121859 (New Zealand LiDAR 1 m DEM).

    An API key is required and can be generated at
    https://data.linz.govt.nz/my/api/.  Pass it directly or set the
    ``LINZ_API_KEY`` environment variable.

    Args:
        api_key: LINZ Data Service API key.  Falls back to the
            ``LINZ_API_KEY`` environment variable when ``None``.
        layer_id: Koordinates layer ID. Defaults to ``121859``.
        timeout_s: HTTP request timeout in seconds.
    """

    def __init__(
        self,
        api_key: str | None = None,
        layer_id: int = _LINZ_LAYER_ID,
        timeout_s: float = _LINZ_TIMEOUT_S,
    ) -> None:
        resolved_key = api_key or os.environ.get("LINZ_API_KEY", "")
        if not resolved_key:
            msg = (
                "A LINZ API key is required. "
                "Pass api_key= or set the LINZ_API_KEY environment variable."
            )
            raise ValueError(msg)
        self._api_key = resolved_key
        self._layer_id = layer_id
        self._timeout_s = timeout_s
        self._session = requests.Session()
        self._session.headers["Accept-Encoding"] = "gzip"

    def get_elevation(self, lat: float, lon: float) -> float:
        """Query the LINZ 1 m DEM for the elevation at a coordinate.

        Args:
            lat: Latitude in decimal degrees (WGS 84).
            lon: Longitude in decimal degrees (WGS 84).

        Returns:
            Elevation above sea level in metres, or ``0.0`` if no data
            is available at the queried location.
        """
        params = {
            "key": self._api_key,
            "layer": self._layer_id,
            "x": lon,
            "y": lat,
        }
        response = self._session.get(
            _LINZ_BASE_URL,
            params=params,
            timeout=self._timeout_s,
        )
        response.raise_for_status()
        data = response.json()
        return _parse_raster_elevation(data, self._layer_id)


def _parse_raster_elevation(data: dict, layer_id: int) -> float:
    """Extract the elevation value from a Koordinates raster query response.

    Args:
        data: Parsed JSON response from the raster query endpoint.
        layer_id: The layer ID to look up in the response.

    Returns:
        Elevation in metres, or ``0.0`` when the layer/band data is absent.
    """
    layer_key = str(layer_id)
    layers = data.get("rasterQuery", {}).get("layers", {})
    layer = layers.get(layer_key, {})
    bands = layer.get("bands", {})
    band_1, *_ = bands
    value = band_1.get("value")
    if value is None:
        logger.warning("No elevation data for query; returning 0.0")
        return 0.0
    return float(value)


def add_elevation_to_graph(
    graph: nx.MultiDiGraph,
    provider: ElevationProvider,
) -> nx.MultiDiGraph:
    """Add elevation attributes to every node in a graph.

    Args:
        graph: OSMnx street network graph.
        provider: Elevation provider used to query each node.

    Returns:
        The same graph with an ``elevation`` attribute on each node.
    """
    for node, data in graph.nodes(data=True):
        lat = data.get("y", 0.0)
        lon = data.get("x", 0.0)
        graph.nodes[node]["elevation"] = provider.get_elevation(float(lat), float(lon))
    return graph

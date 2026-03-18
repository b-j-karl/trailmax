"""Elevation providers for TrailMax route optimisation."""

from abc import ABC, abstractmethod

import networkx as nx


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

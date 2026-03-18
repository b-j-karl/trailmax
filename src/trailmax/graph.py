"""Graph construction and utilities for TrailMax route optimisation."""

from typing import Literal

import networkx as nx
import osmnx as ox

NZ_LAT_MIN = -47.6
NZ_LAT_MAX = -34.1
NZ_LON_MIN = 165.9
NZ_LON_MAX = 178.6


def is_in_new_zealand(lat: float, lon: float) -> bool:
    """Check whether a coordinate lies within the New Zealand bounding box.

    Args:
        lat: Latitude in decimal degrees.
        lon: Longitude in decimal degrees.

    Returns:
        ``True`` if the point is inside the NZ bounding box.
    """
    return NZ_LAT_MIN <= lat <= NZ_LAT_MAX and NZ_LON_MIN <= lon <= NZ_LON_MAX


def build_graph(
    lat: float,
    lon: float,
    radius_m: float = 5000.0,
    network_type: Literal["walk", "bike", "drive", "all"] = "walk",
) -> nx.MultiDiGraph:
    """Download and build a walkable street-network graph from OpenStreetMap.

    Args:
        lat: Latitude of the centre point.
        lon: Longitude of the centre point.
        radius_m: Search radius in metres. Defaults to 5000.
        network_type: OSMnx network type. Defaults to ``"walk"``.

    Returns:
        OSMnx ``MultiDiGraph`` with ``length`` attributes on each edge.
    """
    graph: nx.MultiDiGraph = ox.graph_from_point(
        (lat, lon),
        dist=radius_m,
        network_type=network_type,
        simplify=True,
    )
    return ox.distance.add_edge_lengths(graph)


def get_nearest_node(graph: nx.MultiDiGraph, lat: float, lon: float) -> int:
    """Return the graph node closest to a given lat/lon point.

    Args:
        graph: OSMnx street network graph.
        lat: Query latitude in decimal degrees.
        lon: Query longitude in decimal degrees.

    Returns:
        Node ID of the nearest node.
    """
    node: int = ox.nearest_nodes(graph, lon, lat)
    return node


def compute_edge_weights(
    graph: nx.MultiDiGraph,
    elevation_weight: float = 0.1,
) -> nx.MultiDiGraph:
    """Add a composite ``weight`` attribute to every edge in the graph.

    The weight combines the edge length with an elevation-based penalty
    to discourage excessively steep segments.

    Args:
        graph: OSMnx graph with ``length`` and optional ``grade`` attributes.
        elevation_weight: Penalty multiplier applied to the grade. Defaults
            to 0.1.

    Returns:
        The same graph with a ``weight`` attribute on each edge.
    """
    for _u, _v, _k, data in graph.edges(keys=True, data=True):
        length = float(data.get("length", 1.0))
        grade = abs(float(data.get("grade", 0.0)))
        data["weight"] = length * (1.0 + elevation_weight * grade)
    return graph

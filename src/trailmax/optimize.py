"""Route optimisation engine for TrailMax."""

import random

import networkx as nx

from trailmax.elevation import (
    ElevationProvider,
    MockElevationProvider,
    add_elevation_to_graph,
)
from trailmax.graph import build_graph, compute_edge_weights, get_nearest_node
from trailmax.metrics import (
    compute_elevation_gain_m,
    objective_error,
    total_distance_km,
)
from trailmax.models import RouteRequest, RouteResult, RouteType

_NUM_CANDIDATES = 20
_MAX_PATH_ATTEMPTS = 50


def _node_coords(graph: nx.MultiDiGraph, node: int) -> tuple[float, float]:
    data = graph.nodes[node]
    return float(data["y"]), float(data["x"])


def _path_to_geometry(
    graph: nx.MultiDiGraph, path: list[int]
) -> list[tuple[float, float]]:
    return [_node_coords(graph, node) for node in path]


def _path_elevations(graph: nx.MultiDiGraph, path: list[int]) -> list[float]:
    return [float(graph.nodes[node].get("elevation", 0.0)) for node in path]


def _find_path(
    graph: nx.MultiDiGraph,
    source: int,
    target: int,
) -> list[int] | None:
    """Find the shortest weighted path, returning ``None`` if unreachable."""
    if not nx.has_path(graph, source, target):
        return None
    result: list[int] = nx.shortest_path(graph, source, target, weight="weight")
    return result


def _generate_loop_route(  # noqa: PLR0913
    graph: nx.MultiDiGraph,
    start_node: int,
    target_distance_km: float,
    target_elevation_m: float,
    rng: random.Random,
    num_candidates: int = _NUM_CANDIDATES,
) -> tuple[list[int], float]:
    """Sample random waypoints and return the loop route with lowest error.

    Args:
        graph: Street network graph with ``weight`` attributes.
        start_node: Node ID of the route start/end.
        target_distance_km: Desired total distance in kilometres.
        target_elevation_m: Desired elevation gain in metres.
        rng: Seeded random number generator.
        num_candidates: Maximum number of waypoints to evaluate.

    Returns:
        Tuple of ``(best_path, best_objective_error)``.
    """
    all_nodes = list(graph.nodes())
    best_path: list[int] = [start_node]
    best_error = float("inf")

    for _ in range(min(num_candidates, _MAX_PATH_ATTEMPTS)):
        waypoint = rng.choice(all_nodes)
        if waypoint == start_node:
            continue
        path_out = _find_path(graph, start_node, waypoint)
        if path_out is None:
            continue
        path_back = _find_path(graph, waypoint, start_node)
        if path_back is None:
            continue
        full_path = path_out + path_back[1:]
        geometry = _path_to_geometry(graph, full_path)
        distance = total_distance_km(geometry)
        elevations = _path_elevations(graph, full_path)
        gain = compute_elevation_gain_m(elevations)
        error = objective_error(distance, gain, target_distance_km, target_elevation_m)
        if error < best_error:
            best_error = error
            best_path = full_path

    return best_path, best_error


def _generate_out_and_back_route(  # noqa: PLR0913
    graph: nx.MultiDiGraph,
    start_node: int,
    target_distance_km: float,
    target_elevation_m: float,
    rng: random.Random,
    num_candidates: int = _NUM_CANDIDATES,
) -> tuple[list[int], float]:
    """Sample random turnaround points and return the best out-and-back route.

    Args:
        graph: Street network graph with ``weight`` attributes.
        start_node: Node ID of the route start.
        target_distance_km: Desired total distance in kilometres.
        target_elevation_m: Desired elevation gain in metres.
        rng: Seeded random number generator.
        num_candidates: Maximum number of turnaround nodes to evaluate.

    Returns:
        Tuple of ``(best_path, best_objective_error)``.
    """
    all_nodes = list(graph.nodes())
    best_path: list[int] = [start_node]
    best_error = float("inf")

    for _ in range(min(num_candidates, _MAX_PATH_ATTEMPTS)):
        turnaround = rng.choice(all_nodes)
        if turnaround == start_node:
            continue
        path_out = _find_path(graph, start_node, turnaround)
        if path_out is None:
            continue
        full_path = path_out + list(reversed(path_out[:-1]))
        geometry = _path_to_geometry(graph, full_path)
        distance = total_distance_km(geometry)
        elevations = _path_elevations(graph, full_path)
        gain = compute_elevation_gain_m(elevations)
        error = objective_error(distance, gain, target_distance_km, target_elevation_m)
        if error < best_error:
            best_error = error
            best_path = full_path

    return best_path, best_error


class RouteOptimizer:
    """Optimises running routes using OSMnx graph data and elevation.

    Args:
        elevation_provider: Provider for elevation lookups. Defaults to
            :class:`~trailmax.elevation.MockElevationProvider`.
        seed: Integer random seed for reproducible results.
        num_candidates: Number of candidate routes to evaluate per run.
    """

    def __init__(
        self,
        elevation_provider: ElevationProvider | None = None,
        seed: int | None = None,
        num_candidates: int = _NUM_CANDIDATES,
    ) -> None:
        self._elevation_provider = elevation_provider or MockElevationProvider()
        self._seed = seed
        self._num_candidates = num_candidates

    def optimise(
        self,
        request: RouteRequest,
        graph: nx.MultiDiGraph | None = None,
        start_node: int | None = None,
    ) -> RouteResult:
        """Optimise a route for the given request parameters.

        Downloads an OSMnx graph from OpenStreetMap if ``graph`` is not
        provided.

        Args:
            request: Route request containing start location and targets.
            graph: Pre-built OSMnx graph. Downloads from OSM if ``None``.
            start_node: Graph node to use as route start. Computed from
                ``request.start_lat``/``start_lon`` if not given.

        Returns:
            :class:`~trailmax.models.RouteResult` with the best route found.
        """
        rng = random.Random(self._seed)

        if graph is None:
            graph = build_graph(
                request.start_lat,
                request.start_lon,
                radius_m=request.graph_radius_m,
            )

        graph = add_elevation_to_graph(graph, self._elevation_provider)
        graph = compute_edge_weights(graph)

        if start_node is None:
            start_node = get_nearest_node(graph, request.start_lat, request.start_lon)
        route_type: RouteType = request.constraints.route_type

        if route_type == "loop":
            path, error = _generate_loop_route(
                graph,
                start_node,
                request.target_distance_km,
                request.target_elevation_m,
                rng,
                self._num_candidates,
            )
        else:
            path, error = _generate_out_and_back_route(
                graph,
                start_node,
                request.target_distance_km,
                request.target_elevation_m,
                rng,
                self._num_candidates,
            )

        geometry = _path_to_geometry(graph, path)
        distance = total_distance_km(geometry)
        elevations = _path_elevations(graph, path)
        gain = compute_elevation_gain_m(elevations)

        return RouteResult(
            geometry=geometry,
            distance_km=distance,
            elevation_gain_m=gain,
            route_type=route_type,
            objective_error=error,
            diagnostics={
                "num_nodes": float(len(path)),
                "target_distance_km": request.target_distance_km,
                "target_elevation_m": request.target_elevation_m,
            },
        )


def optimize_route(
    request: RouteRequest,
    graph: nx.MultiDiGraph | None = None,
    elevation_provider: ElevationProvider | None = None,
    seed: int | None = None,
    start_node: int | None = None,
) -> RouteResult:
    """Convenience function to optimise a route.

    Args:
        request: Route request containing start location and targets.
        graph: Pre-built OSMnx graph. Downloads from OSM if ``None``.
        elevation_provider: Elevation provider. Defaults to
            :class:`~trailmax.elevation.MockElevationProvider`.
        seed: Integer random seed for reproducible results.
        start_node: Graph node to use as route start. Computed from
            ``request.start_lat``/``start_lon`` if not given.

    Returns:
        :class:`~trailmax.models.RouteResult` with the best route found.
    """
    optimizer = RouteOptimizer(
        elevation_provider=elevation_provider,
        seed=seed,
    )
    return optimizer.optimise(request, graph=graph, start_node=start_node)

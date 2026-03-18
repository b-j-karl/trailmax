"""Tests for trailmax.optimize module."""

import random

import networkx as nx
import pytest

from trailmax.models import RouteConstraints, RouteRequest
from trailmax.optimize import (
    RouteOptimizer,
    _generate_loop_route,
    _generate_out_and_back_route,
    optimize_route,
)


def make_test_graph() -> nx.MultiDiGraph:
    """Return a small fully-connected graph around central Auckland."""
    nodes = {
        0: {"x": 174.763, "y": -36.848, "elevation": 0.0},
        1: {"x": 174.764, "y": -36.847, "elevation": 10.0},
        2: {"x": 174.765, "y": -36.848, "elevation": 15.0},
        3: {"x": 174.764, "y": -36.849, "elevation": 5.0},
        4: {"x": 174.763, "y": -36.847, "elevation": 8.0},
    }
    edges = [
        (0, 1, {"length": 200.0, "weight": 200.0}),
        (1, 0, {"length": 200.0, "weight": 200.0}),
        (1, 2, {"length": 150.0, "weight": 150.0}),
        (2, 1, {"length": 150.0, "weight": 150.0}),
        (2, 3, {"length": 180.0, "weight": 180.0}),
        (3, 2, {"length": 180.0, "weight": 180.0}),
        (3, 0, {"length": 200.0, "weight": 200.0}),
        (0, 3, {"length": 200.0, "weight": 200.0}),
        (0, 4, {"length": 160.0, "weight": 160.0}),
        (4, 0, {"length": 160.0, "weight": 160.0}),
        (4, 1, {"length": 140.0, "weight": 140.0}),
        (1, 4, {"length": 140.0, "weight": 140.0}),
    ]
    graph = nx.MultiDiGraph()
    for node_id, attrs in nodes.items():
        graph.add_node(node_id, **attrs)
    for u, v, attrs in edges:
        graph.add_edge(u, v, **attrs)
    return graph


@pytest.fixture
def test_graph() -> nx.MultiDiGraph:
    """Fixture providing a small deterministic test graph."""
    return make_test_graph()


def test_generate_loop_route_starts_and_ends_at_same_node(test_graph):
    rng = random.Random(42)
    path, _ = _generate_loop_route(test_graph, 0, 1.0, 0.0, rng)
    assert path[0] == path[-1]


def test_generate_out_and_back_route_is_palindrome(test_graph):
    rng = random.Random(42)
    path, _ = _generate_out_and_back_route(test_graph, 0, 1.0, 0.0, rng)
    assert path == list(reversed(path))


def test_loop_route_type_in_result(test_graph):
    request = RouteRequest(
        start_lat=-36.848,
        start_lon=174.763,
        target_distance_km=1.0,
        constraints=RouteConstraints(route_type="loop"),
    )
    result = optimize_route(request, graph=test_graph, seed=42, start_node=0)
    assert result.route_type == "loop"


def test_out_and_back_route_type_in_result(test_graph):
    request = RouteRequest(
        start_lat=-36.848,
        start_lon=174.763,
        target_distance_km=1.0,
        constraints=RouteConstraints(route_type="out_and_back"),
    )
    result = optimize_route(request, graph=test_graph, seed=42, start_node=0)
    assert result.route_type == "out_and_back"


def test_deterministic_mode_same_seed(test_graph):
    request = RouteRequest(
        start_lat=-36.848,
        start_lon=174.763,
        target_distance_km=1.0,
    )
    result_a = optimize_route(request, graph=test_graph, seed=7, start_node=0)
    result_b = optimize_route(request, graph=test_graph, seed=7, start_node=0)
    assert result_a.geometry == result_b.geometry


def test_different_seeds_may_differ():
    request = RouteRequest(
        start_lat=-36.848,
        start_lon=174.763,
        target_distance_km=1.0,
    )
    optimizer = RouteOptimizer(seed=999, num_candidates=20)
    result = optimizer.optimise(request, graph=make_test_graph(), start_node=0)
    assert result.distance_km >= 0.0


def test_result_diagnostics_keys(test_graph):
    request = RouteRequest(
        start_lat=-36.848,
        start_lon=174.763,
        target_distance_km=1.0,
    )
    result = optimize_route(request, graph=test_graph, seed=0, start_node=0)
    assert "num_nodes" in result.diagnostics
    assert "target_distance_km" in result.diagnostics
    assert "target_elevation_m" in result.diagnostics

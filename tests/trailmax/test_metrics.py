"""Tests for trailmax.metrics module."""

import pytest

from trailmax.metrics import (
    compute_elevation_gain_m,
    compute_grade_pct,
    haversine_distance,
    objective_error,
    total_distance_km,
)


def test_haversine_distance_same_point():
    result = haversine_distance(-36.8485, 174.7633, -36.8485, 174.7633)
    assert result == pytest.approx(0.0)


def test_haversine_distance_known_value():
    # Auckland to Wellington is approximately 490 km
    dist = haversine_distance(-36.8485, 174.7633, -41.2865, 174.7762)
    assert dist == pytest.approx(490.0, rel=0.05)


def test_total_distance_km_empty():
    assert total_distance_km([]) == pytest.approx(0.0)


def test_total_distance_km_single_point():
    assert total_distance_km([(-36.8485, 174.7633)]) == pytest.approx(0.0)


def test_total_distance_km_two_points():
    dist = total_distance_km([(-36.8485, 174.7633), (-36.8585, 174.7633)])
    assert dist > 0.0


def test_compute_elevation_gain_m_flat():
    assert compute_elevation_gain_m([100.0, 100.0, 100.0]) == pytest.approx(0.0)


def test_compute_elevation_gain_m_ascending():
    gain = compute_elevation_gain_m([0.0, 50.0, 100.0])
    assert gain == pytest.approx(100.0)


def test_compute_elevation_gain_m_mixed():
    # Only positive differences should be counted
    gain = compute_elevation_gain_m([0.0, 50.0, 20.0, 80.0])
    assert gain == pytest.approx(110.0)


def test_compute_grade_pct_zero_distance():
    assert compute_grade_pct(0.0, 10.0, 0.0) == pytest.approx(0.0)


def test_compute_grade_pct_uphill():
    assert compute_grade_pct(0.0, 10.0, 100.0) == pytest.approx(10.0)


def test_objective_error_perfect_match():
    error = objective_error(10.0, 200.0, 10.0, 200.0)
    assert error == pytest.approx(0.0)


def test_objective_error_distance_only_deviation():
    # Achieved 5 km vs target 10 km; elevation matches.
    error = objective_error(5.0, 200.0, 10.0, 200.0)
    assert error == pytest.approx(0.25)


def test_objective_error_zero_elevation_target():
    # When target elevation is 0 the elevation term is ignored.
    error = objective_error(10.0, 0.0, 10.0, 0.0)
    assert error == pytest.approx(0.0)


def test_objective_error_weights():
    # When elevation_weight is zero, only the distance term contributes.
    error = objective_error(
        5.0, 0.0, 10.0, 200.0, distance_weight=1.0, elevation_weight=0.0
    )
    assert error == pytest.approx(0.5)

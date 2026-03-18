"""Data models for TrailMax route optimisation."""

from typing import Literal

from pydantic import BaseModel, Field

RouteType = Literal["loop", "out_and_back"]
SurfacePreference = Literal["any", "paved", "unpaved"]


class RouteConstraints(BaseModel):
    """Constraints applied when generating a route.

    Attributes:
        route_type: Whether to generate a loop or out-and-back route.
        max_grade_pct: Maximum allowable grade as a percentage.
        surface_preference: Preferred road surface type.
    """

    route_type: RouteType = "loop"
    max_grade_pct: float = Field(default=30.0, ge=0.0, le=100.0)
    surface_preference: SurfacePreference = "any"


class RouteRequest(BaseModel):
    """Parameters for a route optimisation request.

    Attributes:
        start_lat: Start latitude in decimal degrees.
        start_lon: Start longitude in decimal degrees.
        target_distance_km: Desired total route distance in kilometres.
        target_elevation_m: Desired total elevation gain in metres.
        constraints: Optional routing constraints.
        graph_radius_m: Radius in metres for OSMnx graph download.
    """

    start_lat: float = Field(ge=-90.0, le=90.0)
    start_lon: float = Field(ge=-180.0, le=180.0)
    target_distance_km: float = Field(gt=0.0)
    target_elevation_m: float = Field(default=0.0, ge=0.0)
    constraints: RouteConstraints = Field(default_factory=RouteConstraints)
    graph_radius_m: float = Field(default=5000.0, gt=0.0)


class RouteResult(BaseModel):
    """Result of a route optimisation.

    Attributes:
        geometry: Ordered list of (latitude, longitude) coordinate pairs.
        distance_km: Total route distance in kilometres.
        elevation_gain_m: Total elevation gain in metres.
        route_type: Whether the route is a loop or out-and-back.
        objective_error: Weighted error between achieved and target metrics.
        diagnostics: Additional diagnostic values from the optimiser.
    """

    geometry: list[tuple[float, float]]
    distance_km: float
    elevation_gain_m: float
    route_type: RouteType
    objective_error: float
    diagnostics: dict[str, float]

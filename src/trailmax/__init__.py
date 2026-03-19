"""TrailMax: NZ running route optimiser."""

from trailmax.elevation import LinzElevationProvider
from trailmax.models import RouteConstraints, RouteRequest, RouteResult, RouteType
from trailmax.optimize import RouteOptimizer, optimize_route

__version__ = "0.1.0"

__all__ = [
    "LinzElevationProvider",
    "RouteConstraints",
    "RouteOptimizer",
    "RouteRequest",
    "RouteResult",
    "RouteType",
    "optimize_route",
]

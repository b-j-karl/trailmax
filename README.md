# TrailMax

**Optimise running routes in New Zealand** using OpenStreetMap data and
elevation-aware heuristics. Provide a start location, target distance and
elevation gain, and TrailMax constructs the best matching route from the
local walking network.

> **Future work:** A FastAPI + map frontend is planned; the current release is
> a CLI / Python library only.

---

## Features

- Loop and out-and-back route generation
- Objective function that minimises weighted distance + elevation error
- Pluggable elevation interface (`ElevationProvider`) — stub included, real
  NZ elevation source can be added later
- Deterministic results via optional random seed
- GeoJSON output (stdout + optional file save)
- New Zealand bounds validation

---

## Quickstart

### Install

```bash
pip install trailmax
# or, from source:
pip install -e ".[dev,test]"
```

### CLI

```bash
# 10 km loop around Auckland CBD with 200 m elevation gain
trailmax --start-lat -36.8485 --start-lon 174.7633 \
    --distance-km 10 --elev-m 200 --loop

# 5 km out-and-back from Wellington, save to file, reproducible
trailmax --start-lat -41.2865 --start-lon 174.7762 \
    --distance-km 5 --out-and-back --seed 42 \
    --output wellington_route.geojson
```

Output is a GeoJSON `Feature` printed to stdout:

```json
{
  "type": "Feature",
  "properties": {
    "distance_km": 9.87,
    "elevation_gain_m": 193.4,
    "route_type": "loop",
    "objective_error": 0.031,
    "num_waypoints": 312
  },
  "geometry": {
    "type": "LineString",
    "coordinates": [[174.7633, -36.8485], ...]
  }
}
```

### Python API

```python
from trailmax import LinzElevationProvider, RouteRequest, RouteConstraints, optimize_route
from trailmax.graph import build_graph

request = RouteRequest(
    start_lat=-36.8485,
    start_lon=174.7633,
    target_distance_km=10.0,
    target_elevation_m=200.0,
    constraints=RouteConstraints(route_type="loop"),
)
provider = LinzElevationProvider()
graph = build_graph(request.start_lat, request.start_lon)

result = optimize_route(request, provider, graph, seed=42)
print(f"Distance: {result.distance_km:.1f} km")
print(f"Elevation gain: {result.elevation_gain_m:.0f} m")
print(f"Objective error: {result.objective_error:.3f}")
```

#### Custom elevation provider

```python
from trailmax.elevation import ElevationProvider
from trailmax import optimize_route, RouteRequest
from trailmax.graph import build_graph

class MyNZElevationProvider(ElevationProvider):
    def get_elevation(self, lat: float, lon: float) -> float:
        # Call your DEM / LINZ API here
        return 0.0

request = RouteRequest(
    start_lat=-36.8485, start_lon=174.7633, target_distance_km=10.0
)
result = optimize_route(
    request,
    elevation_provider=MyNZElevationProvider(),
    graph=build_graph(request.start_lat, request.start_lon),
    seed=42,
)
```

---

## Repository structure

```
src/trailmax/
├── __init__.py       # Public API re-exports
├── models.py         # RouteRequest, RouteResult, RouteConstraints
├── graph.py          # OSMnx graph download, NZ bounds check, edge weights
├── elevation.py      # ElevationProvider ABC + LinzElevationProvider
├── optimize.py       # Heuristic optimiser (loop & out-and-back)
├── metrics.py        # Haversine distance, elevation gain, objective error
└── cli.py            # Typer CLI entrypoint
tests/trailmax/
├── test_metrics.py   # Unit tests for metrics module
└── test_optimize.py  # Unit tests for optimiser (loop, out-and-back, seeded)
```

---

## Limitations & next steps

- **Elevation data** – `LinzElevationProvider` queries the LINZ 1 m DEM.
  Ensure a valid ``LINZ_API_KEY`` is set in your environment.
- **Graph caching** – OSM data is re-downloaded on each call. Add a local
  cache with `osmnx.settings.use_cache = True`.
- **Optimisation quality** – the current heuristic samples random waypoints.
  A better approach would weight waypoints by their distance from the start
  to target the desired route length more precisely.
- **Surface filtering** – `surface_preference` is stored in the request but
  not yet used to filter graph edges.
- **Web frontend** – a FastAPI + Leaflet.js interface is planned.

---

## Development

```bash
# Bootstrap
pip install uv==0.8.3
uv sync

# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check .
uv run ruff format .
```

---

## License

MIT


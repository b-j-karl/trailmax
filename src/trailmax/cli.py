"""Command-line interface for the TrailMax route optimiser."""

import json
from pathlib import Path

import typer

from trailmax.graph import is_in_new_zealand
from trailmax.models import RouteConstraints, RouteRequest, RouteType
from trailmax.optimize import optimize_route

app = typer.Typer(
    name="trailmax",
    help="TrailMax: optimise running routes in New Zealand.",
    add_completion=False,
)


@app.command()
def main(  # noqa: PLR0913
    start_lat: float = typer.Option(
        ..., "--start-lat", help="Start latitude (NZ: -47.6 to -34.1)."
    ),
    start_lon: float = typer.Option(
        ..., "--start-lon", help="Start longitude (NZ: 165.9 to 178.6)."
    ),
    distance_km: float = typer.Option(
        ..., "--distance-km", help="Target route distance in kilometres."
    ),
    elev_m: float = typer.Option(
        0.0, "--elev-m", help="Target elevation gain in metres."
    ),
    loop: bool = typer.Option(  # noqa: FBT001
        False,  # noqa: FBT003
        "--loop/--out-and-back",
        help="Generate a loop route (default: out-and-back).",
    ),
    max_grade: float = typer.Option(
        30.0, "--max-grade", help="Maximum allowed grade percentage."
    ),
    surface: str = typer.Option(
        "any",
        "--surface",
        help="Surface preference: any, paved, or unpaved.",
    ),
    radius_m: float = typer.Option(
        5000.0, "--radius-m", help="OSMnx graph search radius in metres."
    ),
    seed: int | None = typer.Option(
        None, "--seed", help="Random seed for reproducible results."
    ),
    output: Path | None = typer.Option(
        None, "--output", help="Path to save GeoJSON output file."
    ),
) -> None:
    r"""Optimise a running route in New Zealand.

    Prints a GeoJSON Feature to stdout and optionally saves it to a file.

    Examples::

        trailmax --start-lat -36.8485 --start-lon 174.7633 \
            --distance-km 10 --elev-m 200 --loop

        trailmax --start-lat -41.2865 --start-lon 174.7762 \
            --distance-km 5 --out-and-back --seed 42
    """
    if not is_in_new_zealand(start_lat, start_lon):
        msg = (
            f"Coordinates ({start_lat}, {start_lon}) are outside "
            "New Zealand. TrailMax only supports NZ routes."
        )
        typer.echo(msg, err=True)
        raise typer.Exit(code=1)

    route_type: RouteType = "loop" if loop else "out_and_back"
    constraints = RouteConstraints(
        route_type=route_type,
        max_grade_pct=max_grade,
        surface_preference=surface,  # type: ignore[arg-type]
    )
    request = RouteRequest(
        start_lat=start_lat,
        start_lon=start_lon,
        target_distance_km=distance_km,
        target_elevation_m=elev_m,
        constraints=constraints,
        graph_radius_m=radius_m,
    )

    result = optimize_route(request, seed=seed)

    geojson: dict[str, object] = {
        "type": "Feature",
        "properties": {
            "distance_km": result.distance_km,
            "elevation_gain_m": result.elevation_gain_m,
            "route_type": result.route_type,
            "objective_error": result.objective_error,
            "num_waypoints": len(result.geometry),
            "diagnostics": result.diagnostics,
        },
        "geometry": {
            "type": "LineString",
            "coordinates": [[lon, lat] for lat, lon in result.geometry],
        },
    }

    output_str = json.dumps(geojson, indent=2)
    typer.echo(output_str)

    if output is not None:
        output.write_text(output_str, encoding="utf-8")
        typer.echo(f"GeoJSON saved to {output}", err=True)

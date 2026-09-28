#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Offered as Corresponding Source for the CARI-derived shoreline geometry
# distributed with Oh Tidepool. See licenses/cari/README.md and COPYING.
"""Fetch a dense, source-attributed CARI rocky-shore outline for one site.

The California Aquatic Resources Inventory (CARI) publishes statewide ``RS``
(Rocky Shore) polygons through an ArcGIS FeatureServer.  This script is an
*offline curation/import utility*, not a request-path dependency.  It writes a
static mapped rocky-intertidal outline that is intentionally separate from the
tide-band waterline/exposure artifacts produced by ``generate_contours.py``.

The source geometry is selected by its intersection with a small local radius
around a named site.  It is not clipped: retaining the original rings avoids
inventing a circular or rectangular edge at the crop boundary.  A conservative
local-meter simplification (0-2 m) can reduce duplicate vertices without
turning a surveyed/modeled curve into a four-corner approximation.

Example:
  python scripts/import_cari_rocky_shore.py \
    --site-id bird-rock-reef --latitude 32.811482 --longitude -117.270771 \
    --radius-meters 350 --simplify-meters 1 \
    --output contour-candidates/cari/bird-rock-reef.geojson

The output is derived from CARI v3.3, which is GPL-3.0-or-later.  Preserve the
embedded attribution, source attributes, and license information when storing
or distributing the output.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from shapely.geometry import Point, shape
from shapely.ops import transform


CARI_ENDPOINT = (
    "https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/"
    "biosds2835_fpu/FeatureServer/0/query"
)
CARI_DATA_URL = "https://www.sfei.org/data/california-aquatic-resource-inventory-cari-gis-data"
CARI_LICENSE_URL = "https://www.gnu.org/licenses/gpl-3.0.html"
CARI_CITATION = (
    "San Francisco Estuary Institute (SFEI). 2026. California Aquatic Resource "
    "Inventory (CARI), version 3.3. Accessed {accessed}."
)
CARI_DATASET_DATE = "2026-02-19"  # CARI v3.3 publication/last-update date.
CARI_DISCLAIMER = (
    "Static modeled rocky-intertidal habitat context, not a tide-specific waterline, "
    "surveyed boundary, navigational chart, safe route, or real-time access condition."
)


def local_meters_per_degree(latitude: float) -> tuple[float, float]:
    """Return WGS84 meters/degree at latitude for a sub-kilometer local frame."""
    latitude_radians = math.radians(latitude)
    meters_per_latitude = (
        111_132.92
        - 559.82 * math.cos(2 * latitude_radians)
        + 1.175 * math.cos(4 * latitude_radians)
        - 0.0023 * math.cos(6 * latitude_radians)
    )
    meters_per_longitude = (
        111_412.84 * math.cos(latitude_radians)
        - 93.5 * math.cos(3 * latitude_radians)
        + 0.118 * math.cos(5 * latitude_radians)
    )
    return meters_per_latitude, meters_per_longitude


def fetch_json(request_url: str) -> dict[str, Any]:
    """Fetch a public ArcGIS response, backing off briefly on transient errors."""
    last_error: Exception | None = None
    for attempt in range(4):
        try:
            with urlopen(request_url, timeout=60) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code not in {429, 500, 502, 503, 504}:
                raise
            last_error = error
        except URLError as error:
            last_error = error
        if attempt < 3:
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"CARI request failed after retries: {last_error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-id", required=True)
    parser.add_argument("--latitude", required=True, type=float)
    parser.add_argument("--longitude", required=True, type=float)
    parser.add_argument(
        "--radius-meters",
        type=float,
        default=350.0,
        help="Select source polygons that intersect this local radius (default: 350).",
    )
    parser.add_argument(
        "--simplify-meters",
        type=float,
        default=1.0,
        help="Local-meter Douglas-Peucker tolerance, from 0 to 2 (default: 1).",
    )
    parser.add_argument("--output", required=True, help="Destination GeoJSON path")
    return parser.parse_args()


def local_transformers(latitude: float, longitude: float):
    """Return WGS84↔local-meter transforms centered on one site.

    An equirectangular local frame has sub-centimeter scale error over the
    350-meter defaults used here, while avoiding a hidden dependency on a
    projection database.  It is only used for selection and simplification;
    source coordinates are written back in WGS84.
    """
    meters_per_degree_latitude, meters_per_degree_longitude = local_meters_per_degree(latitude)

    def to_local(x, y, z=None):
        local_x = (x - longitude) * meters_per_degree_longitude
        local_y = (y - latitude) * meters_per_degree_latitude
        return (local_x, local_y) if z is None else (local_x, local_y, z)

    def to_wgs84(x, y, z=None):
        geographic_x = x / meters_per_degree_longitude + longitude
        geographic_y = y / meters_per_degree_latitude + latitude
        return (geographic_x, geographic_y) if z is None else (geographic_x, geographic_y, z)

    return to_local, to_wgs84


def request_geojson(latitude: float, longitude: float, radius_meters: float) -> list[dict[str, Any]]:
    """Fetch all CARI Rocky Shore polygons in a radius-sized query envelope."""
    if radius_meters <= 0:
        raise ValueError("--radius-meters must be positive")
    meters_per_latitude, meters_per_longitude = local_meters_per_degree(latitude)
    lat_delta = radius_meters / meters_per_latitude
    lon_delta = radius_meters / meters_per_longitude
    geometry = ",".join(
        str(value)
        for value in (
            longitude - lon_delta,
            latitude - lat_delta,
            longitude + lon_delta,
            latitude + lat_delta,
        )
    )
    params: dict[str, Any] = {
        "f": "geojson",
        "where": "legcode = 'RS'",
        "geometry": geometry,
        "geometryType": "esriGeometryEnvelope",
        "inSR": 4326,
        "outSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "resultRecordCount": 2000,
    }
    features: list[dict[str, Any]] = []
    offset = 0
    while True:
        page_params = {**params, "resultOffset": offset}
        request_url = f"{CARI_ENDPOINT}?{urlencode(page_params)}"
        payload = fetch_json(request_url)
        if "error" in payload:
            raise RuntimeError(f"CARI request failed: {payload['error']}")
        page = payload.get("features", [])
        features.extend(page)
        if not payload.get("exceededTransferLimit") or not page:
            return features
        offset += len(page)


def select_and_simplify(
    features: list[dict[str, Any]],
    *,
    latitude: float,
    longitude: float,
    radius_meters: float,
    simplify_meters: float,
    site_id: str,
) -> list[dict[str, Any]]:
    """Select source polygons touching the local radius and preserve their rings."""
    to_local, to_wgs84 = local_transformers(latitude, longitude)
    selection = Point(0, 0).buffer(radius_meters)
    selected: list[dict[str, Any]] = []
    for feature in features:
        source_geometry = shape(feature["geometry"])
        local_geometry = transform(to_local, source_geometry)
        if local_geometry.is_empty or not local_geometry.intersects(selection):
            continue
        simplified = local_geometry.simplify(simplify_meters, preserve_topology=True) if simplify_meters else local_geometry
        if simplified.is_empty:
            continue
        original_properties = feature.get("properties", {})
        source_id = feature.get("id") or original_properties.get("OBJECTID") or original_properties.get("objectid")
        selected.append(
            {
                "type": "Feature",
                "id": str(source_id) if source_id is not None else None,
                "properties": {
                    "site_id": site_id,
                    "source_feature_id": source_id,
                    "source_dataset": "California Aquatic Resources Inventory (CARI) v3.3",
                    "source_class": original_properties.get("clicklabel", "Rocky Shore"),
                    "source_legcode": original_properties.get("legcode", "RS"),
                    "source_attributes": original_properties,
                },
                "geometry": transform(to_wgs84, simplified).__geo_interface__,
            }
        )
    return selected


def geometry_counts(geometry: dict[str, Any]) -> tuple[int, int, int]:
    """Return polygon, ring, and coordinate counts without flattening holes."""
    geometry_type = geometry.get("type")
    if geometry_type == "Polygon":
        rings = geometry["coordinates"]
        return 1, len(rings), sum(len(ring) for ring in rings)
    if geometry_type == "MultiPolygon":
        totals = [geometry_counts({"type": "Polygon", "coordinates": polygon}) for polygon in geometry["coordinates"]]
        return tuple(sum(values[index] for values in totals) for index in range(3))  # type: ignore[return-value]
    if geometry_type == "GeometryCollection":
        totals = [geometry_counts(child) for child in geometry.get("geometries", [])]
        return tuple(sum(values[index] for values in totals) for index in range(3))  # type: ignore[return-value]
    return 0, 0, 0


def main() -> None:
    args = parse_args()
    if not -90 <= args.latitude <= 90 or not -180 <= args.longitude <= 180:
        raise SystemExit("--latitude/--longitude must be valid WGS84 coordinates")
    if not 0 <= args.simplify_meters <= 2:
        raise SystemExit("--simplify-meters must be between 0 and 2")
    raw_features = request_geojson(args.latitude, args.longitude, args.radius_meters)
    features = select_and_simplify(
        raw_features,
        latitude=args.latitude,
        longitude=args.longitude,
        radius_meters=args.radius_meters,
        simplify_meters=args.simplify_meters,
        site_id=args.site_id,
    )
    if not features:
        raise SystemExit(
            f"No CARI Rocky Shore geometry intersects {args.radius_meters:g} m of {args.site_id}; "
            "check the site coordinate or increase the radius."
        )
    accessed_at = datetime.now(timezone.utc).isoformat()
    output = {
        "type": "FeatureCollection",
        "properties": {
            "site_id": args.site_id,
            "dataset_name": "California Aquatic Resources Inventory (CARI) v3.3",
            "source_url": CARI_DATA_URL,
            "dataset_date": CARI_DATASET_DATE,
            # CARI combines modeled and source data at variable resolution;
            # unknown is safer than falsely claiming its detailed rings are a
            # new 1 m survey.
            "resolution_meters": None,
            "provenance": "official-gis",
            "outline_kind": "rocky-intertidal",
            "geometry_status": "exploratory",
            "disclaimer": CARI_DISCLAIMER,
            "coordinate": {"latitude": args.latitude, "longitude": args.longitude},
            "selection_radius_meters": args.radius_meters,
            "selection_method": (
                "Original CARI Rocky Shore polygons intersecting a local-radius buffer; "
                "geometry is selected, not crop-clipped."
            ),
            "simplify_meters": args.simplify_meters,
            "source": {
                "dataset_name": "California Aquatic Resources Inventory (CARI) v3.3",
                "publisher": "San Francisco Estuary Institute",
                "endpoint": CARI_ENDPOINT,
                "dataset_url": CARI_DATA_URL,
                "license": "GPL-3.0-or-later",
                "license_url": CARI_LICENSE_URL,
                "citation": CARI_CITATION.format(accessed=accessed_at[:10]),
                "accessed_at": accessed_at,
            },
        },
        "features": features,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, separators=(",", ":")))
    counts = [geometry_counts(feature["geometry"]) for feature in features]
    print(
        json.dumps(
            {
                "site_id": args.site_id,
                "queried_feature_count": len(raw_features),
                "selected_feature_count": len(features),
                "polygon_count": sum(item[0] for item in counts),
                "ring_count": sum(item[1] for item in counts),
                "vertex_count": sum(item[2] for item in counts),
                "output": str(output_path),
            }
        )
    )


if __name__ == "__main__":
    main()

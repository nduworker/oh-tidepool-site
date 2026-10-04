# CARI Corresponding Source

This directory is the **Corresponding Source** for the CARI-derived shoreline
geometry that is bundled in the Oh Tidepool iOS app. It is offered under
**GPL-3.0-or-later** (SPDX: `GPL-3.0-or-later`), matching the licence of the
upstream CARI dataset. See [`COPYING.txt`](COPYING.txt) for the full licence text.

## What is here

| Path | Contents |
| --- | --- |
| `index.html` | The public page for this directory, which the app's licence text links to |
| `outlines/<site-id>.geojson` | The 18 derived rocky-shore outlines shipped in the app's bundled catalog |
| `scripts/import_cari_rocky_shore.py` | The importer that produced them (SPDX: `GPL-3.0-or-later`) |
| `COPYING.txt` | GNU General Public License v3.0 |

## Upstream source and attribution

- Dataset: **California Aquatic Resources Inventory (CARI) v3.3**, `RS`
  (Rocky Shore) polygons.
- Publisher: San Francisco Estuary Institute (SFEI).
- Landing page: <https://www.sfei.org/data/california-aquatic-resource-inventory-cari-gis-data>
- ArcGIS source used: `biosds2835_fpu/FeatureServer/0/query`.
- Licence: GPL-3.0-or-later, <https://www.gnu.org/licenses/gpl-3.0.html>.
- Citation: San Francisco Estuary Institute (SFEI). 2026. California Aquatic
  Resources Inventory (CARI), version 3.3. Accessed 2026-09-18.

## Transformation applied

The importer selects the CARI `RS` polygons that intersect a 350 m radius
around each site's reviewed anchor and applies a 1 m Douglas-Peucker
simplification in a local metre frame. Geometry is written back in WGS84 as
GeoJSON. Nothing is clip-cropped, so the original ring edges are preserved
rather than replaced with a fabricated circular boundary.

## Regenerate

```sh
python3 -m venv .venv-contours
.venv-contours/bin/pip install shapely
.venv-contours/bin/python licenses/cari/scripts/import_cari_rocky_shore.py \
  --site-id bird-rock-reef --latitude 32.811482 --longitude -117.270771 \
  --radius-meters 350 --simplify-meters 1 \
  --output licenses/cari/outlines/bird-rock-reef.geojson
```

This geometry is a static mapped rocky-intertidal boundary, **never** a predicted waterline,
navigational chart, safe route, or real-time access condition.

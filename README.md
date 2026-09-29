# Oh Tidepool public site

This repository intentionally contains only the public Oh Tidepool landing page,
privacy policy, and the app's published content. The landing page is published
with GitHub Pages at `https://oh-tidepool.nduwork.com/`.

The iPhone app source, development documentation, credentials, and operations
materials remain in the separate private application repository.

## App content

The app reads its content over HTTPS from the raw `main` branch origin, so no
Pages deployment is needed to make a content change visible:

```text
https://raw.githubusercontent.com/nduworker/oh-tidepool-site/main/
```

| Path | Purpose |
| --- | --- |
| `data/index.json` | The app's only unconditional request. Its `ETag` makes the common refresh body-free (`304`). |
| `data/media.json` | Integrity manifest for the reviewed image renditions. |
| `data/daily-conditions.json` | Optional daily briefing, absent until committed. |
| `data/welfare-topics.json` | Optional reviewed welfare topics the app rotates as an in-app banner. Fetched directly by the app, so it is not listed in `index.json` and moves no revision. |
| `media/<asset-id>-v<revision>.webp` | Reviewed renditions. The iPhone catalog resolves ID `bat-star` revision `1` as `media/bat-star-v1.webp`. |
| `schemas/`, `scripts/` | The data contract, its read-only validator, and the local manifest generator. |
| `licenses/cari/` | GPL-3.0-or-later Corresponding Source for the CARI-derived shoreline geometry shipped in the app. |
| `licenses.html` | Public licences, attributions, and data-source page linked from every page footer. |

Same-revision overwrites are allowed: the app and its cache verify each file's
SHA-256 from `data/media.json`, not the filename, so a replaced file at the same
path is picked up once the regenerated manifest is committed with it. The raw
origin's CDN may serve the previous bytes for a few minutes; the app rejects the
mismatch and retries. Third-party renditions still get a new revision in the app
catalog.

See [`data/README.md`](data/README.md) for the authoring and validation workflow,
the daily report rules, and the cross-file revision agreements.

## Demo clips

The clips in `demo/` are built from simulator recordings of the shipped app, not
made by hand. [`scripts/build-demo-clips.py`](scripts/build-demo-clips.py) trims
the idle head and tail of a recording, cuts the loop to the scenario's window,
scales to twice the figure's rendered width, and writes an H.264 clip with its
poster frame.

```sh
python3 scripts/build-demo-clips.py --scenario where --input ~/Desktop/where.mov
python3 scripts/build-demo-clips.py --scenario where --input ~/Desktop/where.mov --check
```

Video rather than GIF: eight seconds of the same screen cost well under a
megabyte as a clip against two or three as a GIF, and the motion keeps the
recording's frame rate instead of a palette. `--window-seconds 0` keeps the whole
capture, which is how the current three clips were built from the earlier GIFs.

Each scenario has its own timing because a scroll and a tap read at different
speeds. A recording may run longer than the window; the script cuts the loop to
the window, which is what keeps the page inside its byte budget.

| Scenario | What the recording shows | Window | Budget |
| --- | --- | --- | --- |
| `where` | The Explore list scrolled, then the same sites on the map | 8s + 1s hold | 0.7 MB |
| `when` | A site page: the day's guidance, hazard bullets, current tide and surf, the tide chart | 8s + 1s hold | 0.7 MB |
| `what` | A discovery site with estimated guidance | 6s + 1s hold | 0.6 MB |
| `tips` | The tip row in the Explore header: swipe on, swipe back, tap to open | 7s + 1s hold | 0.6 MB |

`tips` has no clip yet; it lands with its first recording. The other three still
show the 27 September captures, which predate the tip row and the day's guidance,
until new recordings of the current build replace them.

The recordings are produced in the private application repository, at the
simulator's own resolution. The script downscales, so record full size. Record
from a run that carries the states the scenario needs: a caution beside an
otherwise good day, a hazard bullet that says what the hazard does to a visit,
and a cited local story labelled Unofficial. Keep the status bar at a plausible
time, and leave out system alerts and permission prompts.

The [`Validate public data`](.github/workflows/validate-public-data.yml) workflow
is a read-only integrity check. It does not fetch provider data, generate a
report, process images, modify files, commit, push, or deploy. A commit touching
only `media/**` does not start it.

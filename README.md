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

Video rather than GIF. The same screens cost 2.2 MB as four clips and posters
where the three retired GIFs cost 12.6 MB, and the motion keeps the recording's
frame rate instead of a palette. `--window-seconds 0` keeps a whole capture.

Each scenario has its own window and hold, because a scroll and a tap do not need
the same run-up. A recording may run longer than the window; the script cuts the
loop to the window, which is what keeps the page inside its byte budget.

| Scenario | What the clip shows | Window | Budget | Size |
| --- | --- | --- | --- | --- |
| `where` | The Explore list, then the same sites on the map | last 14s + 1s hold | 1.4 MB | 0.41 MB |
| `when` | Dike Rock's published guidance, the caution beside a good day, the hazard bullets, the tide chart | 68s + 18s, +1s hold | 1.6 MB | 0.76 MB |
| `what` | La Jolla Cove, a discovery site: estimated guidance | last 8s + 1s hold | 0.8 MB | 0.42 MB |
| `tips` | The tip row: swiped on, swiped back, then opened with its source | 19s + 14s, +1s hold | 1.0 MB | 0.22 MB |

Two settings are pinned to moments a script cannot detect: `start_s`, for a clip
that begins at a swipe rather than at the first movement, and `poster_at`, for the
frame shown before the clip plays. Both were read off the 29 September captures
by sampling each recording at 1 fps and reading the frames with `tesseract`, and
both need checking against a new recording.

Two things bite when re-cutting these, and both cost a wasted clip the first
time:

- `-ss` has to come after `-i`. Seeking before the input on these recordings
  lands tens of seconds away from the moment asked for, because QuickTime's edit
  list does not survive the fast seek. The script decodes up to the moment
  instead, which costs a few seconds per build.
- Check the built clip, not the source. Sample its own frames and read them, the
  same way the windows were chosen. A clip can look right in the summary and
  still show the wrong seconds of the recording.
- Read the caption against the clip. "Tide forecast" can be the row that opens a
  disclosure rather than the chart inside it; a caption that promises the chart
  needs a recording that opens it.

The recordings are produced in the private application repository, at the
simulator's own resolution, by `ios/OhTidepoolUITests/DemoCaptureTests.swift`.
Each run asserts the screen its scenario needs before it stops, so the screen the
clip needs is up when the run ends and nobody captures the wrong one. The script
downscales, so record at full size. Keep the status bar at a plausible time, and
leave out system alerts and permission prompts.

The [`Validate public data`](.github/workflows/validate-public-data.yml) workflow
is a read-only integrity check. It does not fetch provider data, generate a
report, process images, modify files, commit, push, or deploy. A commit touching
only `media/**` does not start it.

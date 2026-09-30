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

The five clips in `demo/` are cut from simulator recordings of the shipped app,
not made by hand. [`scripts/build-demo-clips.py`](scripts/build-demo-clips.py)
trims a recording, cuts the loop to a scenario window, scales to twice the
figure's rendered width and writes an H.264 clip with its poster frame.

```sh
python3 scripts/build-demo-clips.py --scenario where --input ~/Desktop/where.mov
python3 scripts/build-demo-clips.py --settles --scenario where --input ~/Desktop/where.mov
```

`--settles` lists the runs where the screen is not moving. Every window below
starts and ends on one of those runs, because a loop that begins mid-gesture and
ends mid-transition reads as a glitch rather than a demonstration. That was the
fault in the first cut of these clips, and it is why the windows are chosen from
the settle report rather than from a fixed duration.

Two things about the recordings that cost a wasted cut the first time:

- They are variable frame rate: the simulator writes a frame when the screen
  changes, so a window can average 8 fps in a burst-pause pattern. Encoding that
  as-is drops frames and the motion stutters. The script encodes **30 fps
  constant**, which keeps every frame and duplicates only the ones already still.
- `-ss` has to come after `-i`. Seeking before the input on these recordings
  lands tens of seconds away from the moment asked for, because QuickTime's edit
  list does not survive the fast seek.

Windows, all read off the 30 September takes with `--settles` and `tesseract`:

| Scenario | What the clip shows | Window | Size |
| --- | --- | --- | --- |
| `where` | The list with both ribbon kinds, then the same sites on the map | 35.25s for 14.75s | 0.43 MB |
| `when` | Dike Rock: "Limited - go with care" with the cue "Surf too high", the hazard bullets, then the chart | 30s for 16.5s | 0.21 MB |
| `what` | La Jolla Cove, a discovery site: the estimate from a nearby gauge | 63.25s for 10.35s | 0.71 MB |
| `tips` | The tip row: swiped to the next tip, swiped back, then opened with its source | 20.25s for 11.95s | 0.21 MB |
| `alerts` | The Alerts tab: the plan-visit card and what it watches | 22.75s for 14.5s | 0.21 MB |

Every clip is verified by reading its own frames back, never the summary: the
content check reads one frame per second with `tesseract`, and the ends are
measured for motion, which is the check that caught two windows ending in a
scroll. The only motion left in a first or last half second is the tip row's own
drifting chevrons, which is the app animating rather than a cut.

The [`Validate public data`](.github/workflows/validate-public-data.yml) workflow
is a read-only integrity check. It does not fetch provider data, generate a
report, process images, modify files, commit, push, or deploy. A commit touching
only `media/**` does not start it.

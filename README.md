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

## Public-page design and content

The site is a free, education-first field guide. See [DESIGN.md](DESIGN.md) for
its hierarchy, source ownership, responsive behavior and accessibility decisions.
There are no client-side scripts, analytics, signup forms or external fonts.

The directory, animal profiles and photo attributions were checked against the
app's bundled catalogs at `882dd2a`. Recheck them when the app's locations or
reviewed content change; the landing page does not automatically mirror those
catalogs. The three tips come from `data/welfare-topics.json`, reviewed
2026-09-29. Images are existing, manifest-tracked renditions in `media/`.
No media manifest, schema or CARI source changes are needed for their reuse.

The page explains predictions but does not publish a current forecast. The
focused `demo/dike-rock-tide-chart.webp` screenshot shows the actual curve,
NOAA basis and orange 1.0 ft guide; it was captured by the app session and is
explicitly dated, like every recording. The optional daily briefing can expire and has
neither the full catalog nor the tide-chart series, so it is not repurposed into
an improvised live forecast here.

## Demo clips

[`scripts/build-demo-clips.py`](scripts/build-demo-clips.py) cuts continuous
windows from simulator recordings, scales them to 600px and writes H.264 clips
and posters. The page uses three clips in context, with native play/pause
controls and written descriptions. No clip autoplays. The discovery and alerts
clips remain available for future editorial use, but are not loaded by this page.

```sh
python3 scripts/build-demo-clips.py --scenario tips --input ~/Desktop/tips.mov
python3 scripts/build-demo-clips.py --settles --scenario tips --input ~/Desktop/tips.mov
```

`--settles` reports candidate quiet runs. It samples coarse thumbnails and is
not proof of a settled boundary; verify the *built clip* at full cadence and
read its frames. The tips take is now cut from 19s for 14s, before the sheet
closes, with no extension. Its first and last second are quiet. The configured source interval is 14s;
the resulting file reports 13.33s, so measure the output rather than treating
the configured interval as its encoded duration.

Output is normalized to 30 fps. Constant-rate conversion can duplicate or drop
frames; it cannot reconstruct missing motion or fix an abrupt cut. Earlier
claims that it keeps every source frame or proves the cause of the owner's
quality complaint were not supported. Also, the old `when` clip reveals the
Tide chart heading, not the curve itself; the page's description says so.

`-ss` stays after `-i`: fast input seeking on these takes previously produced
the wrong screen. `hold_s` currently extends the source interval; it does not
freeze a frame. Keep any extension inside a verified quiet run.

## Page checks

```sh
python3 -m unittest discover -s tests -v
python3 scripts/validate-public-data.py
git diff --check
```

The page tests check local asset/link integrity, accessible video defaults,
semantic structure, the full site directory and explicit free/beta wording.
Browser geometry, native controls, keyboard navigation and accessibility must
also be checked at phone, tablet and desktop sizes after layout changes.

The [`Validate public data`](.github/workflows/validate-public-data.yml) workflow
is a read-only integrity check. It does not fetch provider data, generate a
report, process images, modify files, commit, push, or deploy. A commit touching
only `media/**` does not start it.

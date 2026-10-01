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

This is an app-first landing page for free educational outreach. The official
icon and real Explore/tide-chart UI lead the page. App uses, field-guide UI,
reviewed tips and optional alerts explain what Oh Tidepool offers. The page
has no standalone site directory, animal-photo gallery, client scripts,
analytics, signup forms or external fonts. See [DESIGN.md](DESIGN.md).

Catalog counts and image credits were checked against the app's bundled catalogs
at `882dd2a`: 14 sites and 4 reviewed Tidepool guides. The public tips payload
contains 68 reviewed tips. Recheck these counts when app content changes.

Website-only icon renditions are in `assets/`; app screenshots are in `demo/`.
The Explore still comes from `where.mov` at 16s. The chart, Dike Rock species
list and anemone photo view come from focused app XCUITest captures. Screenshot
renditions were checked by reading their own text, not a capture summary.
Screens show recorded 30 September 2026 examples, not today's forecast or a
sightings promise. The photo view is not described as a separate profile page.

`app-media-credits.html` retains creator/source/licence and derivative notices
for the reviewed photographs appearing within app UI. The UI/icon itself is
Oh Tidepool artwork. Public payloads, manifest media and CARI source are unchanged.

The page explains predictions but does not publish current conditions. The
optional daily briefing can expire and does not contain a full tide-chart series,
so it is not turned into a live web forecast here.

## Demo clips

[`scripts/build-demo-clips.py`](scripts/build-demo-clips.py) cuts continuous
windows from simulator recordings, scales them to 600px and writes H.264 clips
and posters. The page uses two clips in context, with native play/pause
controls and written descriptions. No clip autoplays. This page uses the
Explore and tips clips. Discovery, day-guidance and Alerts recordings remain
available locally but are not loaded. The Alerts UI still describes surf filtering,
which contradicts the current scheduler; do not use that demo to illustrate the
implemented tide/weather criteria. The app owner is handling its copy separately.

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
quality complaint were not supported. The old `when` clip reveals only a
Tide chart heading; the focused chart screenshot provides the actual curve.

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
semantic structure, real icon/UI placement, removal of the standalone photo
showcases, app-use content and explicit free/beta wording.
Browser geometry, native controls, keyboard navigation and accessibility must
also be checked at phone, tablet and desktop sizes after layout changes.

The [`Validate public data`](.github/workflows/validate-public-data.yml) workflow
is a read-only integrity check. It does not fetch provider data, generate a
report, process images, modify files, commit, push, or deploy. A commit touching
only `media/**` does not start it.

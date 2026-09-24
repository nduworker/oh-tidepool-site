# Oh Tidepool public site

This repository intentionally contains only the public Oh Tidepool landing page,
privacy policy, and the app's published content. The landing page is published
with GitHub Pages at `https://nduworker.github.io/oh-tidepool-site/`.

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
| `media/<asset-id>-v<revision>.webp` | Reviewed renditions. The iPhone catalog resolves ID `bat-star` revision `1` as `media/bat-star-v1.webp`. |
| `schemas/`, `scripts/` | The data contract, its read-only validator, and the local manifest generator. |

Same-revision overwrites are allowed: the app and its cache verify each file's
SHA-256 from `data/media.json`, not the filename, so a replaced file at the same
path is picked up once the regenerated manifest is committed with it. The raw
origin's CDN may serve the previous bytes for a few minutes; the app rejects the
mismatch and retries. Third-party renditions still get a new revision in the app
catalog.

See [`data/README.md`](data/README.md) for the authoring and validation workflow,
the daily report rules, and the cross-file revision agreements.

The [`Validate public data`](.github/workflows/validate-public-data.yml) workflow
is a read-only integrity check. It does not fetch provider data, generate a
report, process images, modify files, commit, push, or deploy. A commit touching
only `media/**` does not start it.

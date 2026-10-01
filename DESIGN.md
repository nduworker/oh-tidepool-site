# Oh Tidepool public site

## Purpose
A free, education-first field companion. The public page should teach something
useful even when a visitor never installs the app. No account or email funnel.
The beta invitation is available, not the organizing principle of the page.

## Design thesis
A small world, worth slowing down for. Move from curiosity to a nearby shore,
from a tide chart to understanding exposure, from noticing an animal to leaving
its home undisturbed. Use real shore photographs and reviewed field-guide
content rather than abstract feature icons or a wall of phone demos.

## Information architecture
```
Brand / Shores / Free iPhone beta
  Curiosity: real shore photograph + invitation to explore
  Four chapter links
  01 Find your shore: four reviewed guides + ten Discovery estimates
  02 Read the tide: exposure, cautions, estimate basis + recorded chart
  03 Look closer: six real field-guide inhabitants, no sightings promise
  04 Leave it wild: three reviewed tips with their sources + recorded tip row
  Free public TestFlight beta / feedback
  Full photograph attributions / privacy / licences / contact
```
The first three things to convey: this is a real Southern California shore,
there is a small world worth noticing, and visitors can learn before installing.

## Evidence and ownership
- Directory names, regions, guide introductions and profile photographs:
  app `ios/OhTidepool/Resources/bundled-tidepools.json` and
  `bundled-discoveries.json`, inspected at app commit `882dd2a`.
- Four site-reviewed Tidepool guides, ten Discovery sites. Discovery windows
  use a nearby gauge and borrowed tide guide; never style them as equally certain.
- Six animal photographs, scientific names and descriptions: the same catalogs'
  `species_profiles`. These are examples of field-guide content, not sightings.
- Tips: `data/welfare-topics.json`, ids `look-dont-touch`, `do-not-turn-rocks`,
  `leave-it-cleaner`. Preserve their text and source links.
- Image paths: `data/media.json`. Visible credit disclosure includes creator,
  original source, licence link and derivative notice for every displayed asset.
- Dated app recordings are examples, never current predictions. Do not render
  the optional daily briefing as current data on this page: it expires and does
  not include the full site catalog or tide series.

## Visual system
- Warm sand `#f7f0df`, paper `#fffdf6`, ink `#113d4b`, deep teal `#075d6d`,
  foam `#e3f5ef`, coral `#ba3d1d`, muted ink `#456571`.
- Native serif display: Iowan Old Style / Palatino / Georgia. Body: Avenir Next /
  Avenir / Trebuchet MS. No external font requests or analytics.
- Spacing vocabulary: 8, 12, 16, 20, 24, 32, 40, 64, 88, 96 px.
- Editorial hierarchy, thin rules, numbered chapters, unambiguous kind labels.
  No decorative badges for every feature. Animal photographs remain square.
- One landscape photograph leads; contextual, user-played recordings support
  the story. No autoplay, no looping distractions, no animation dependency.

## Responsive and accessibility
- Mobile: compact brand/beta header, copy before a landscape shore photograph,
  a two-by-two chapter index, full-width guide entries, single-column directory,
  a two-column animal gallery (one below 350px), readable clips at 280px.
- Desktop: copy/photo opening spread; two guide columns; compact two-column
  discovery directory; three animal columns; explanation and demo side-by-side.
- Semantic landmarks, one h1, ordered headings, skip link, descriptive alt text,
  visible focus ring, link names and text alternatives for silent demos.
- Native video controls provide play/pause/seek and work without JavaScript.
  Default is a still poster, including for reduced-motion users.
- Interactive hit areas at least 44px; body contrast at least WCAG AA.
- No required JavaScript. A broken/offline video retains its poster and written
  description. Long names wrap, rather than truncate away the identity of a shore.
- Photo credit disclosure opens with a native keyboard-accessible details control.

## State decisions
| Element | Initial | Interaction | Missing/offline |
| --- | --- | --- | --- |
| Directory | All fourteen sites visible | Visitor-information links for reviewed guides | Text remains useful even if photos fail |
| Recordings | Poster and written description | Native controls; visitor initiates motion | Description remains; no dependency on playback |
| Photo credits | Compact disclosure | Native details opens the complete attribution list | Fully inline; no fetched credits |
| Beta | Free, TestFlight, iPhone, testing status explicit | Public Apple join link | No site account or signup fallback |

## Not in scope
- Live site predictions or a fabricated tide curve: leave these to the app and
  its provider/expiry handling. The page explains how to interpret them instead.
- A public web version of the app, geolocation, signup, analytics or marketing
  tracking: unnecessary for education and outreach.
- App catalog/schema edits and `licenses/cari/`: retain their existing ownership.
- Visual-score claims without seeing screenshots. Browser measurements can
  establish geometry and accessibility; a human must judge image crops and taste.

# Oh Tidepool landing page

## Approved direction
An app-first page for free educational outreach. The owner rejected the previous
standalone tidepool directory and photo galleries. Visitors should immediately
recognize Oh Tidepool, see its actual interface, and understand what they can use
it for. No sales funnel, account signup or standalone nature showcase.

## Hierarchy
1. Official app icon and name; clear free iPhone/TestFlight status.
2. Real Explore and tide-chart UI, alongside the headline:
   "Know when to go. Learn what to notice."
3. Five app-supported outcomes: find a place, plan around the tide, identify
   shoreline life, learn thoughtful visiting habits, and plan optional alerts.
4. Authentic "What to look for" UI from the app, not an animal-photo gallery.
5. A reviewed-tip demonstration with native controls, plus optional alerts in prose.
6. Free outreach purpose, honest planning limits, beta instructions and feedback.
7. Privacy, licences, app image credits and contact.

The site list, animal profiles and tips belong to the app. The public page explains
those features with app UI; it does not replicate their content as a second guide.

## Responsive composition
- Desktop: copy and two recognizable app screens in the opening spread.
- On mobile, the headline is followed by the Explore screen, then the
  introduction and beta action. The DOM uses the same order, so keyboard focus
  follows the visible composition.
  The chart follows the app-use list at full readable width instead of becoming
  a tiny second phone. The header keeps a beta link visible in the opening view.
- The field-guide module combines a short explanation with its real screen.
  Reviewed tips and optional-alert explanations sit beside the actual tip demo;
  mobile stacks these without an obsolete Alerts screen.
- Each still screen links to its full-size rendition. No invented phone notch,
  floating forecast card, simulated chart or UI recreated in HTML.

## Visual system
Retain sand `#f7f0df`, ink `#113d4b`, deep teal `#075d6d`, foam `#e3f5ef`, coral
`#ba3d1d`, paper `#fffdf6` and muted ink `#456571`. Serif headlines and native
Avenir/Trebuchet body fonts require no external font request. Use thin rules,
short explanations, numbered outcomes and actual app imagery.

## Evidence and asset ownership
- Icon: official `Assets.xcassets/AppIcon.appiconset/Icon-1024.png` in the app;
  resized website renditions in `assets/`. These are not new app-manifest assets.
- Explore still: source `where.mov` at 16s. Its own900px rendition was OCR-read.
- Chart: focused app XCUITest capture `dike-rock-tide-chart.png`.
- Field guide: fresh focused XCUITest capture `dike-rock-species-guide.png`,
  showing Dike Rock, "What to look for", animal/scientific names and descriptions.
- Photo view: `aggregating-anemone-detail.png`, with its in-app attribution.
  Describe this as a photo view, not a separate profile page with invented text.
- Still screenshots were captured 30 September 2026. Keep capture provenance
  in these authoring docs, not in visitor-facing labels. App previews need no
  repeated capture dates or "not today's forecast" warnings. Dates within actual
  app UI remain untouched; the page still explains estimates and planning limits.
- Two continuous recordings: Explore/map and tips/source sheet.
- Do not show the existing Alerts recording. Its UI says tide/surf filtering,
  while the current scheduler uses tide/weather with surf in warnings. Current
  behavior may be described in prose; app UI copy correction is separate work.
- Catalog counts checked at app commit `882dd2a`:14 sites, 4 site-reviewed guides;
  `data/welfare-topics.json`:68 reviewed tips. Recheck counts when content changes.
- `app-media-credits.html` preserves 39 site/animal image attributions that may
  appear within app screenshots/recordings. No standalone photo gallery.
- Existing manifest media, public payloads, schemas and `licenses/cari/` stay
  unchanged. Site assets in `assets/` and `demo/` are separate from app media.

## Accessibility and states
- Semantic headings, named landmarks, keyboard skip link, visible focus rings.
- At least 44px link/summary targets and WCAG AA text contrast.
- Native user-played, silent videos with pause/seek controls and written
  descriptions. No autoplay or loop, including for reduced-motion visitors.
- A still poster/description is useful if a recording cannot load.
- Alt text describes app UI. Empty alt on the icon avoids repeating the named
  brand link; the repeated beta icon is decorative.
- No client-side scripts, signup, analytics or live-provider dependencies.
- Real recordings are shown directly, not hidden behind a screenshot carousel.

## Limits and approval
This is a free public beta, not an App Store release. The app is a planning aid,
not an official safety decision. Tidepool site guides and borrowed Discovery
estimates must remain distinct; surf cautions must not imply permission or safety.

After implementation: browser-check mobile/tablet/desktop, verify built asset
content and local links, review shared policy styling, run tests/data validation,
and open a PR. Do not deploy before owner approval. No Codex review, per owner
instruction. Human review of screenshots/crops remains necessary because image
vision is unavailable in both collaborating sessions.

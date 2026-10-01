"""Dependency-free regression checks for the app-first public page."""
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.nodes.append((tag, attrs))
        if "id" in attrs:
            self.ids.append(attrs["id"])


class SiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / "index.html").read_text()
        cls.page = Page()
        cls.page.feed(cls.text)

    def test_local_links_assets_and_fragments_resolve(self):
        for tag, attrs in self.page.nodes:
            for key in ("href", "src", "poster"):
                value = attrs.get(key)
                if not value:
                    continue
                parsed = urlsplit(value)
                if parsed.scheme or parsed.netloc:
                    continue
                with self.subTest(value=value):
                    if parsed.path:
                        path = ROOT / unquote(parsed.path)
                        self.assertTrue(path.exists(), value)
                    elif parsed.fragment:
                        self.assertIn(parsed.fragment, self.page.ids)

    def test_structure_and_no_duplicate_ids(self):
        self.assertEqual(len(self.page.ids), len(set(self.page.ids)))
        tags = [tag for tag, _ in self.page.nodes]
        self.assertEqual(tags.count("h1"), 1)
        self.assertEqual(tags.count("main"), 1)
        self.assertIn('class="skip-link"', self.text)

    def test_app_uses_replace_standalone_nature_content(self):
        for heading in ["Find a place to explore", "Plan around the tide",
                        "Learn what you're looking at", "Build thoughtful visiting habits",
                        "Get a reminder to plan your visit"]:
            self.assertIn(heading, self.text)
        for removed_class in ["shore-card", "site-list", "animal-grid", "hero-shore"]:
            self.assertNotIn('class="' + removed_class + '"', self.text)
        self.assertIn("14 mapped sites", self.text)
        self.assertIn("68 reviewed tips", self.text)
        self.assertIn("Best estimate", self.text)
        self.assertIn("What to look for", self.text)
        self.assertIn("not an official safety decision", self.text)

    def test_real_app_icon_and_screens_are_prominent(self):
        self.assertIn('class="app-icon" src="./assets/app-icon.webp"', self.text)
        hero = self.text.split('<section class="app-hero"', 1)[1].split('</section>', 1)[0]
        self.assertIn("./demo/explore-screen.webp", hero)
        self.assertIn("./demo/dike-rock-tide-chart.webp", hero)
        self.assertNotIn("./media/", hero)
        self.assertIn("fetchpriority=\"high\"", hero)
        self.assertIn("./demo/field-guide-screen.webp", self.text)
        self.assertIn("./demo/animal-profile-screen.webp", self.text)

    def test_preview_captions_do_not_add_dates_or_forecast_warnings(self):
        self.assertNotIn("September", self.text)
        self.assertNotIn("today's forecast", self.text)
        self.assertNotIn("recording date", self.text)
        self.assertIn("Tap a screen for the full-size image.", self.text)

    def test_motion_is_opt_in_and_has_text_alternatives(self):
        videos = [a for tag, a in self.page.nodes if tag == "video"]
        self.assertEqual(len(videos), 2)
        for v in videos:
            self.assertIn("controls", v)
            self.assertNotIn("autoplay", v)
            self.assertNotIn("loop", v)
            self.assertEqual(v["preload"], "none")
            self.assertTrue(v.get("aria-label"))
        self.assertNotIn('src="./demo/alerts.mp4"', self.text)
        self.assertEqual(self.text.count('class="demo-transcript"'), len(videos))

    def test_app_screens_have_alt_dimensions_and_image_credits(self):
        images = [a for tag, a in self.page.nodes if tag == "img"]
        for image in images:
            with self.subTest(src=image["src"]):
                if image["src"] == "./assets/app-icon.webp":
                    self.assertIn("alt", image)  # Named brand link supplies its meaning.
                else:
                    self.assertTrue(image.get("alt"))
                self.assertGreater(int(image["width"]), 0)
                self.assertGreater(int(image["height"]), 0)
                self.assertFalse(image["src"].startswith("./media/"))
        self.assertIn("./app-media-credits.html", self.text)
        credits = (ROOT / "app-media-credits.html").read_text()
        self.assertIn("CC BY-SA", credits)
        self.assertIn("Peter Pearsall", credits)
        self.assertIn("marine.gov", credits)

    def test_free_outreach_without_signup_or_script_dependency(self):
        self.assertIn("free app for learning", self.text)
        self.assertIn("not an App Store release", self.text)
        self.assertIn("https://testflight.apple.com/join/pNysjdxG", self.text)
        tags = [tag for tag, _ in self.page.nodes]
        self.assertNotIn("form", tags)
        self.assertNotIn("script", tags)


if __name__ == "__main__":
    unittest.main()

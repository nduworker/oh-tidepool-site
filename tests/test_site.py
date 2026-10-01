"""Dependency-free regression checks for the public field-guide page."""
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

    def test_directory_and_educational_content(self):
        nodes = self.page.nodes
        self.assertEqual(sum(a.get("class") == "shore-card" for _, a in nodes), 4)
        for name in ["Bird Rock reef", "Children's Pool / Casa Beach", "Hospital Point",
                     "La Jolla Cove rocky intertidal", "Ocean Beach Pier reefs",
                     "Shell Beach / Seal Rock", "Sunset Cliffs intertidal benches",
                     "Swami's reef", "Tourmaline / Pacific Beach reef", "Windansea reef"]:
            from html import escape
            self.assertIn(escape(name), self.text)
        self.assertEqual(sum(a.get("class") == "animal" for _, a in nodes), 6)
        self.assertEqual(sum(a.get("class") == "tip" for _, a in nodes), 3)
        self.assertIn("Best estimate", self.text)
        self.assertIn("sightings forecast", self.text)
        self.assertIn("not an official safety decision", self.text)

    def test_motion_is_opt_in_and_has_text_alternatives(self):
        videos = [a for tag, a in self.page.nodes if tag == "video"]
        self.assertEqual(len(videos), 3)
        for v in videos:
            self.assertIn("controls", v)
            self.assertNotIn("autoplay", v)
            self.assertNotIn("loop", v)
            self.assertEqual(v["preload"], "none")
            self.assertTrue(v.get("aria-label"))
        # Each recording and the separate chart screenshot have a text description.
        self.assertEqual(self.text.count('class="demo-transcript"'), len(videos) + 1)
        self.assertEqual(self.text.count("Not today's forecast"), len(videos) + 1)
        self.assertIn("./demo/dike-rock-tide-chart.webp", self.text)

    def test_photos_have_alt_dimensions_and_attribution(self):
        images = [a for tag, a in self.page.nodes if tag == "img"]
        for image in images:
            with self.subTest(src=image["src"]):
                self.assertTrue(image.get("alt"))
                self.assertGreater(int(image["width"]), 0)
                self.assertGreater(int(image["height"]), 0)
        self.assertIn('id="photo-credits"', self.text)
        self.assertIn("CC BY-SA", self.text)
        self.assertIn("Peter Pearsall", self.text)

    def test_free_outreach_without_signup_or_script_dependency(self):
        self.assertIn("free app for learning", self.text)
        self.assertIn("not an App Store release", self.text)
        self.assertIn("https://testflight.apple.com/join/pNysjdxG", self.text)
        tags = [tag for tag, _ in self.page.nodes]
        self.assertNotIn("form", tags)
        self.assertNotIn("script", tags)


if __name__ == "__main__":
    unittest.main()

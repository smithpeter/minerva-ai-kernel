from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SITE = ROOT / "public-site"
INDEX = PUBLIC_SITE / "index.html"


class PublicSiteHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.text_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attributes = dict(attrs)
        href = attributes.get("href")
        if href:
            self.links.append(href)

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.text_chunks.append(text)


def parse_index() -> PublicSiteHTMLParser:
    parser = PublicSiteHTMLParser()
    parser.feed(INDEX.read_text(encoding="utf-8"))
    return parser


class PublicSiteArtifactTests(unittest.TestCase):
    def test_public_site_artifact_exists(self) -> None:
        self.assertTrue(INDEX.is_file())

    def test_public_site_contains_required_minerva_positioning(self) -> None:
        parser = parse_index()
        text = " ".join(parser.text_chunks).lower()

        required_phrases = [
            "minerva ai kernel",
            "cpu-local failure interpreter for ci/cd, agents, and ops",
            "narrow m0 claim",
            "policy-check decision",
            "no remote llm required",
            "does not auto-repair systems",
            "not a full aiops platform",
            "does not replace ci",
            "does not execute arbitrary model-generated shell commands",
        ]

        for phrase in required_phrases:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_public_site_links_to_docs_and_github(self) -> None:
        parser = parse_index()
        links = set(parser.links)

        self.assertIn("https://github.com/smithpeter/minerva-ai-kernel", links)

        required_doc_fragments = [
            "/README.md",
            "/docs/m0-release-readiness.md",
            "/docs/m0-local-release-dry-run.md",
            "/docs/m0-launch-blog-post.md",
            "/docs/integration-recipes.md",
            "/docs/m0-ci-domain-verification-record.md",
        ]

        for fragment in required_doc_fragments:
            with self.subTest(fragment=fragment):
                self.assertTrue(
                    any(fragment in link for link in links),
                    f"missing documentation link containing {fragment}",
                )

    def test_public_site_has_no_rejected_brand_markers(self) -> None:
        rejected_markers = [
            "voxsign",
            "test.voxsign.net",
        ]

        for path in PUBLIC_SITE.rglob("*"):
            if not path.is_file():
                continue
            content = path.read_text(encoding="utf-8", errors="ignore").lower()
            for marker in rejected_markers:
                with self.subTest(path=path.relative_to(ROOT), marker=marker):
                    self.assertNotIn(marker, content)

    def test_public_site_is_standalone_static_html(self) -> None:
        html = INDEX.read_text(encoding="utf-8").lower()

        self.assertNotIn("<script", html)
        self.assertNotIn('rel="stylesheet"', html)
        self.assertNotIn("http://", html)

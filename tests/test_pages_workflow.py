from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "pages.yml"
PUBLIC_SITE = ROOT / "public-site"
CNAME = PUBLIC_SITE / "CNAME"


class PagesWorkflowTests(unittest.TestCase):
    def test_pages_workflow_publishes_public_site(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("actions/upload-pages-artifact@v3", workflow)
        self.assertIn("path: public-site", workflow)
        self.assertIn("actions/deploy-pages@v4", workflow)
        self.assertIn("actions/configure-pages@v5", workflow)
        self.assertIn("enablement: true", workflow)
        self.assertIn("github.event_name == 'workflow_dispatch'", workflow)
        self.assertIn(
            "python3 -m unittest tests.test_public_site_artifact "
            "tests.test_pages_workflow",
            workflow,
        )

    def test_pages_workflow_has_required_permissions(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn("contents: read", workflow)
        self.assertIn("pages: write", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("environment:", workflow)
        self.assertIn("name: github-pages", workflow)

    def test_pages_workflow_avoids_private_server_deployment(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8").lower()

        rejected_markers = [
            "voxsign",
            "test.voxsign.net",
            "49.51.134.101",
            "scp ",
            "rsync ",
            "ssh ",
        ]

        for marker in rejected_markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, workflow)

    def test_custom_domain_artifact_is_present(self) -> None:
        self.assertTrue(CNAME.is_file())
        self.assertEqual("minervakernel.com", CNAME.read_text(encoding="utf-8").strip())

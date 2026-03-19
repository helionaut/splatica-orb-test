from __future__ import annotations

import re
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
RELATIVE_LINK_PATTERN = re.compile(
    r"\[[^]]+\]\((?!https?://|mailto:|#)([^)]+)\)"
)


class PublicationDocsTests(unittest.TestCase):
    def test_readme_links_publication_docs(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("(docs/publication-decision.md)", readme)
        self.assertIn("(docs/PRODUCTION_VERIFICATION.md)", readme)

    def test_publication_decision_captures_current_publish_policy(self) -> None:
        decision = (REPO_ROOT / "docs/publication-decision.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("one concrete publishable artifact", decision)
        self.assertIn("static GitHub Pages publication", decision)
        self.assertIn("artifact-manifest.json", decision)
        self.assertIn("not_useful", decision)
        self.assertIn("make verify-production", decision)
        self.assertIn("https://helionaut.github.io/splatica-orb-test/", decision)

    def test_relative_markdown_links_resolve(self) -> None:
        for relative_path in (
            "README.md",
            "docs/publication-decision.md",
            "docs/PRODUCTION_VERIFICATION.md",
        ):
            source = REPO_ROOT / relative_path
            text = source.read_text(encoding="utf-8")

            for link_target in RELATIVE_LINK_PATTERN.findall(text):
                resolved = (source.parent / link_target).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"{relative_path} references missing {link_target}",
                )

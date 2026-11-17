"""Relative links and anchors in the Markdown documentation resolve."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = [
    ROOT / "README.md",
    ROOT / "tasks/README.md",
    *sorted((ROOT / "docs").glob("*.md")),
]
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)|!\[[^\]]*\]\(([^)\s]+)\)")
HTML = re.compile(r"""(?:src|srcset|href)="([^"]+)\"""")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$", re.MULTILINE)
FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def slug(heading: str) -> str:
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces to hyphens."""
    text = re.sub(r"`|\*|_", "", heading).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    text = FENCE.sub("", path.read_text())
    return {slug(match) for match in HEADING.findall(text)}


def targets(path: Path) -> list[str]:
    text = FENCE.sub("", path.read_text())
    found = [a or b for a, b in LINK.findall(text)]
    found += HTML.findall(text)
    return [t for t in found if not re.match(r"[a-z][a-z0-9+.-]*:", t)]


class DocumentationLinks(unittest.TestCase):
    def test_relative_links_resolve(self):
        problems = []
        for document in DOCUMENTS:
            for target in targets(document):
                file, _, anchor = target.partition("#")
                destination = (document.parent / file).resolve() if file else document
                name = f"{document.relative_to(ROOT)}: {target}"
                if not destination.exists():
                    problems.append(f"{name} (missing file)")
                elif (
                    anchor
                    and destination.suffix == ".md"
                    and anchor not in anchors(destination)
                ):
                    problems.append(f"{name} (missing heading)")
        self.assertEqual(problems, [])

    def test_slug_matches_github(self):
        self.assertEqual(slug("Running the benchmark"), "running-the-benchmark")
        self.assertEqual(slug("Install `websitebench`"), "install-websitebench")
        self.assertEqual(slug("Q&A: setup"), "qa-setup")


if __name__ == "__main__":
    unittest.main()

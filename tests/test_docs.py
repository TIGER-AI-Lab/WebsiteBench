"""The documentation states the same runtime policy as the checker and the tasks."""

from __future__ import annotations

import importlib.util
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/check_tasks.py"
SPEC = importlib.util.spec_from_file_location("check_tasks", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


def toml_block_after(text: str, heading: str) -> dict:
    """Parse the first ```toml block that follows a Markdown heading."""
    section = text[text.index(f"\n{heading}\n") :]
    start = section.index("```toml\n") + len("```toml\n")
    return tomllib.loads(section[start : section.index("```", start)])


class RunningGuide(unittest.TestCase):
    def test_running_md_lists_the_agent_allowlist(self):
        text = (ROOT / "docs/running.md").read_text()
        hosts = toml_block_after(text, "## Agent network")["agent"]["allowed_hosts"]
        self.assertEqual(set(hosts), checks.AGENT_HOSTS)
        task = tomllib.loads((ROOT / "tasks/medium/task.toml").read_text())
        self.assertEqual(hosts, task["agent"]["allowed_hosts"])


if __name__ == "__main__":
    unittest.main()

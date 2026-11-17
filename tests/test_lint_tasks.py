"""The Harbor lint wrapper leaves out only the two known misreadings."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

from harbor.lint.models import LintFinding, LintRule

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/lint_tasks.py"
SPEC = importlib.util.spec_from_file_location("lint_tasks", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
lint = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lint)

LOCKED = (
    "RUN uv pip install --python /usr/local/bin/python --no-deps --require-hashes "
    "--link-mode copy --target /opt/vendor -r /tmp/vendor.requirements.lock\n"
)


class Misreported(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def finding(self, rule, name, line=None, text=""):
        path = self.root / name
        path.write_text(text)
        return LintFinding(rule=rule, path=str(path), message="m", line=line)

    def test_compose_load_failure_is_left_out(self):
        finding = self.finding(LintRule.INVALID_TASK_CONFIG, "docker-compose.yaml")
        self.assertTrue(lint.misreported(finding))

    def test_task_config_errors_are_kept(self):
        finding = self.finding(LintRule.INVALID_TASK_CONFIG, "task.toml")
        self.assertFalse(lint.misreported(finding))

    def test_hash_locked_install_is_left_out(self):
        finding = self.finding(
            LintRule.UNPINNED_PYTHON_DEPENDENCY, "Dockerfile", 2, "FROM x\n" + LOCKED
        )
        self.assertTrue(lint.misreported(finding))

    def test_unpinned_package_is_kept(self):
        text = "FROM x\nRUN pip install requests\n"
        finding = self.finding(
            LintRule.UNPINNED_PYTHON_DEPENDENCY, "Dockerfile", 2, text
        )
        self.assertFalse(lint.misreported(finding))

    def test_other_rules_are_kept(self):
        finding = self.finding(LintRule.AGENT_IMAGE_TEST_LEAK, "Dockerfile", 1, "x\n")
        self.assertFalse(lint.misreported(finding))


if __name__ == "__main__":
    unittest.main()

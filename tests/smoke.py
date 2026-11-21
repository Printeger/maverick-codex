#!/usr/bin/env python3
"""Installer smoke checks. Temporary projects only; no models, network or benchmark."""
import json
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/maverick.py"
ROLES = {"maverick", "rebel", "inventor", "hacker", "scientist", "producer"}
GUIDANCE = "# Existing project\nKeep the established coordinate convention.\n"
CONFIG = '''# Keep this comment and existing settings.
model = "existing-parent-model"
model_reasoning_effort = "high"
[agents]
enabled = true
max_threads = 4
[mcp_servers.project_docs]
command = "existing-docs-command"
args = ["--local"]
'''


def files(project):
    return {str(p.relative_to(project)): p.read_bytes()
            for p in project.rglob("*") if p.is_file()}


class Smoke(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="maverick smoke ")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        (self.project / ".codex").mkdir()
        (self.project / "AGENTS.md").write_text(GUIDANCE)
        (self.project / ".codex/config.toml").write_text(CONFIG)
        (self.project / "app.py").write_text("print('existing application')\n")

    def run_cli(self, command, *args, code=0, installed=False):
        script = self.project / ".agents/skills/maverick/scripts/maverick.py" if installed else SCRIPT
        proc = subprocess.run([sys.executable, str(script), command,
                               "--project", str(self.project), *args],
                              text=True, capture_output=True, timeout=15)
        self.assertEqual(proc.returncode, code, proc.stdout + proc.stderr)
        return json.loads(proc.stdout if code in (0, 2) else proc.stderr)

    def role(self, role):
        return tomllib.loads((self.project / f".codex/agents/mav_{role}.toml").read_text())

    def test_install_preserve_repeat_and_doctor(self):
        result = self.run_cli("init")
        self.assertEqual(result["status"], "installed_needs_adaptation")
        self.assertTrue((self.project / "AGENTS.md").read_text().startswith(GUIDANCE))
        config = (self.project / ".codex/config.toml").read_text()
        self.assertEqual(config, CONFIG)
        self.assertEqual((self.project / "app.py").read_text(), "print('existing application')\n")
        persona_dir = self.project / ".agents/skills/maverick/references/personas"
        self.assertEqual({p.stem for p in persona_dir.glob("*.md")}, ROLES)
        roles = self.project / ".codex/agents"
        self.assertEqual({p.stem for p in roles.glob("*.toml")}, {"mav_" + r for r in ROLES - {"maverick"}})
        for role in ROLES - {"maverick"}:
            data = self.role(role)
            self.assertEqual(data["name"], "mav_" + role)
            self.assertTrue(data["description"] and data["developer_instructions"])
            self.assertNotIn("model", data)
        pending = self.run_cli("doctor", code=2, installed=True)
        self.assertEqual((pending["static"], pending["project_context"]), ("PASS", "PENDING"))
        self.assertEqual(pending["native_runtime"], "NOT_TESTED_BY_DOCTOR")
        for name in ("PROJECT.md", "knowledge/domain.md"):
            path = self.project / ".maverick" / name
            path.write_text("# Fixture\n\nStatus: READY\n\n## Scope\nOne script.\n"
                            "## Evidence\napp.py is the application entry.\n## Command\npython app.py\n")
        ready = self.run_cli("doctor", installed=True)
        self.assertEqual(ready["project_context"], "READY")
        before = files(self.project)
        self.assertEqual(self.run_cli("init")["status"], "already_initialized")
        self.assertEqual(files(self.project), before)

    def test_manual_update_replace_remove_and_sync(self):
        self.run_cli("init")
        args = ("--persona", "hacker", "--key", "simple_change")
        self.run_cli("update", *args, "--rule", "Prefer an existing function.", installed=True)
        self.run_cli("update", *args, "--rule", "Avoid an extra adapter for one caller.", installed=True)
        prefs = json.loads((self.project / ".maverick/preferences.json").read_text())
        self.assertEqual(prefs["hacker"], {"simple_change": "Avoid an extra adapter for one caller."})
        instructions = self.role("hacker")["developer_instructions"]
        self.assertIn("Avoid an extra adapter for one caller.", instructions)
        self.assertNotIn("Prefer an existing function.", instructions)
        self.run_cli("update", *args, "--remove", installed=True)
        self.assertNotIn("Avoid an extra adapter for one caller.", self.role("hacker")["developer_instructions"])
        base = self.project / ".agents/skills/maverick/references/personas/hacker.md"
        base.write_text(base.read_text() + "\nExplain the concrete change first.\n")
        self.run_cli("sync", installed=True)
        self.assertIn("Explain the concrete change first.", self.role("hacker")["developer_instructions"])
        self.assertEqual(len((self.project / ".maverick/updates.jsonl").read_text().splitlines()), 3)

    def test_unowned_collision_leaves_every_file_unchanged(self):
        collision = self.project / ".codex/agents/mav_hacker.toml"
        collision.parent.mkdir()
        collision.write_text('name = "existing-owned-agent"\n')
        before = files(self.project)
        self.assertEqual(self.run_cli("init", code=1)["status"], "ERROR")
        self.assertEqual(files(self.project), before)

    def test_worker_model_is_optional_and_can_return_to_inherit(self):
        self.run_cli("init", "--worker-model", "selected-worker-model")
        self.assertEqual(self.role("hacker")["model"], "selected-worker-model")
        for role in ROLES - {"maverick", "hacker"}:
            self.assertNotIn("model", self.role(role))
        self.assertEqual(tomllib.loads((self.project / ".codex/config.toml").read_text())["model"],
                         "existing-parent-model")
        self.run_cli("sync", "--worker-model", "inherit", installed=True)
        self.assertNotIn("model", self.role("hacker"))


if __name__ == "__main__":
    unittest.main(verbosity=2)

#!/usr/bin/env python3
"""Install, upgrade and ledger checks. Temporary projects only; no models or network."""
import json
import hashlib
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from contributions_smoke import Contributions

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

    def run_cli(self, command, *args, code=0, installed=False, stdin=None, raw=False):
        script = self.project / ".agents/skills/maverick/scripts/maverick.py" if installed else SCRIPT
        proc = subprocess.run([sys.executable, str(script), command,
                               "--project", str(self.project), *args],
                              text=True, capture_output=True, timeout=15, input=stdin)
        self.assertEqual(proc.returncode, code, proc.stdout + proc.stderr)
        return proc.stdout if raw else json.loads(proc.stdout or proc.stderr)

    def role(self, role):
        return tomllib.loads((self.project / f".codex/agents/mav_{role}.toml").read_text())

    def test_install_preserve_repeat_and_doctor(self):
        result = self.run_cli("init")
        self.assertEqual(result["status"], "installed_needs_adaptation")
        self.assertTrue((self.project / "AGENTS.md").read_text().startswith(GUIDANCE))
        config = (self.project / ".codex/config.toml").read_text()
        parsed = tomllib.loads(config)
        self.assertEqual(parsed["model"], "gpt-6.2-sol")
        self.assertEqual(parsed["model_reasoning_effort"], "high")
        self.assertEqual(parsed["agents"]["max_threads"], 4)
        self.assertIn("project_docs", parsed["mcp_servers"])
        self.assertIn("# Keep this comment and existing settings.", config)
        self.assertEqual((self.project / "app.py").read_text(), "print('existing application')\n")
        persona_dir = self.project / ".agents/skills/maverick/references/personas"
        self.assertEqual({p.stem for p in persona_dir.glob("*.md")}, ROLES)
        roles = self.project / ".codex/agents"
        self.assertEqual({p.stem for p in roles.glob("*.toml")}, {"mav_" + r for r in ROLES - {"maverick"}})
        for role in ROLES - {"maverick"}:
            data = self.role(role)
            self.assertEqual(data["name"], "mav_" + role)
            self.assertTrue(data["description"] and data["developer_instructions"])
            self.assertEqual(data["model"], "gpt-6.2-sol")
            self.assertEqual(data["model_reasoning_effort"], "medium" if role in {"hacker", "producer"} else "high")
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

    def test_fixed_models_are_enforced_by_sync_and_doctor(self):
        self.run_cli("init")
        for role in ROLES - {"maverick"}:
            data = self.role(role)
            self.assertEqual(data["model"], "gpt-6.2-sol")
            self.assertEqual(data["model_reasoning_effort"], "medium" if role in {"hacker", "producer"} else "high")
        config = self.project / ".codex/config.toml"
        config.write_text(config.read_text().replace('model = "gpt-6.2-sol"', 'model = "another-model"', 1))
        drift = self.run_cli("doctor", code=1, installed=True)
        self.assertTrue(any("Main model must" in message for message in drift["errors"]))
        self.run_cli("sync", installed=True)
        cfg = tomllib.loads(config.read_text())
        self.assertEqual(cfg["model"], "gpt-6.2-sol")
        self.assertEqual(cfg["model_reasoning_effort"], "high")

    def test_upgrade_preserves_project_data_and_edited_persona(self):
        self.run_cli("init")
        self.run_cli("update", "--persona", "hacker", "--key", "simple", "--rule", "Use the existing function.")
        state = self.project / ".maverick/STATE.md"
        state.write_text("# Current task\nTask ID: useful-work\nKeep this decision and result.\n")
        domain = self.project / ".maverick/knowledge/domain.md"
        domain.write_text("# Actual project knowledge\nPreserve the user's own references.\n")
        base = self.project / ".agents/skills/maverick/references/personas/hacker.md"
        base.write_text(base.read_text() + "\nLocally chosen wording.\n")
        dest = self.project / ".agents/skills/maverick"
        # Simulate an older, owned package file; its recorded baseline permits refresh.
        old_skill = "# Previous installed package\n"
        (dest / "SKILL.md").write_text(old_skill)
        manifest = self.project / ".maverick/manifest.json"
        info = json.loads(manifest.read_text())
        info["managed_files"]["SKILL.md"] = hashlib.sha256(old_skill.encode()).hexdigest()
        info["version"] = "1.1.0"  # Simulate a prior installed version.
        info["worker_model"] = "legacy-worker"
        manifest.write_text(json.dumps(info))
        preserved = {p: p.read_bytes() for p in (state, domain, base,
                     self.project / ".maverick/preferences.json", self.project / ".maverick/updates.jsonl",
                     self.project / ".codex/config.toml", self.project / "app.py")}
        result = self.run_cli("upgrade")
        self.assertEqual(result["version"], "1.1.1")
        self.assertIn(str(base.relative_to(self.project)), result["preserved_local_files"])
        self.assertEqual((dest / "SKILL.md").read_text(), (ROOT / "skills/maverick/SKILL.md").read_text())
        for p, saved in preserved.items():
            if p.name != "config.toml":
                self.assertEqual(p.read_bytes(), saved)
        updated = tomllib.loads((self.project / ".codex/config.toml").read_text())
        self.assertEqual(updated["model"], "gpt-6.2-sol")
        self.assertEqual(updated["model_reasoning_effort"], "high")
        self.assertEqual(updated["agents"]["max_threads"], 4)
        self.assertIn("project_docs", updated["mcp_servers"])
        self.assertIn("Locally chosen wording.", self.role("hacker")["developer_instructions"])
        self.assertIn("Use the existing function.", self.role("hacker")["developer_instructions"])
        self.assertEqual(self.role("hacker")["model"], "gpt-6.2-sol")
        self.assertEqual(self.role("hacker")["model_reasoning_effort"], "medium")
        self.assertNotIn("worker_model", json.loads(manifest.read_text()))
        before = files(self.project)
        self.assertEqual(self.run_cli("upgrade")["status"], "already_current")
        self.assertEqual(files(self.project), before)

    def test_upgrade_conflict_stops_before_writing(self):
        self.run_cli("init")
        skill = self.project / ".agents/skills/maverick/SKILL.md"
        skill.write_text(skill.read_text() + "\nA locally modified framework instruction.\n")
        before = files(self.project)
        result = self.run_cli("upgrade", code=1)
        self.assertIn("Locally edited framework", result["message"])
        self.assertEqual(files(self.project), before)

    def test_doctor_detects_stale_root_instructions(self):
        self.run_cli("init")
        skill = self.project / ".agents/skills/maverick/SKILL.md"
        original = skill.read_text()
        skill.write_text("---\nname: maverick\ndescription: Old routing\n---\nUse old task routing.\n")
        result = self.run_cli("doctor", code=1, installed=True)
        self.assertTrue(any("SKILL.md" in error for error in result["errors"]))
        skill.write_text(original)
        guidance = self.project / "AGENTS.md"
        guidance.write_text(guidance.read_text().replace("Choose a useful thinking mode", "Use an old job rota"))
        result = self.run_cli("doctor", code=1, installed=True)
        self.assertTrue(any("stale or edited Maverick instructions" in error for error in result["errors"]))

    def test_installed_ledger_cli_and_doctor_validation(self):
        self.run_cli("init")
        contribution = {"id": "route", "task": "fix-one", "persona": "rebel", "mode": "perspective",
                        "actor": "maverick", "trigger": "Repeated failure", "kind": "correction",
                        "contribution": "Check the caller's assumption", "status": "proposed",
                        "outcome": "", "evidence": [], "impact": None}
        self.run_cli("record", "--event", "-", installed=True, stdin=json.dumps(contribution))
        pending = self.run_cli("report", "--task", "fix-one", installed=True, raw=True)
        self.assertIn("待验证建议", pending)
        self.assertNotIn("3 · 关键", pending)
        contribution.update(status="confirmed", outcome="The incorrect fallback was removed.",
                            evidence=["app.py: entry point"], impact=2)
        self.run_cli("record", "--event", "-", installed=True, stdin=json.dumps(contribution))
        actual = self.run_cli("report", "--task", "fix-one", installed=True, raw=True)
        self.assertIn("2 · 实质", actual)
        self.assertIn("主对话，非子 Agent", actual)
        self.assertNotIn("待验证建议", actual)
        self.assertEqual(self.run_cli("doctor", code=2, installed=True)["static"], "PASS")
        ledger = self.project / ".maverick/contributions.jsonl"
        before = ledger.read_bytes()
        self.run_cli("upgrade")
        self.assertEqual(ledger.read_bytes(), before)
        with ledger.open("a") as target:
            target.write("{not json}\n")
        bad = self.run_cli("doctor", code=1, installed=True)
        self.assertEqual(bad["static"], "FAIL")
        self.assertTrue(any("line 3" in error for error in bad["errors"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)

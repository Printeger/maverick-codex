#!/usr/bin/env python3
"""Meaningful installer checks, using isolated settings and fake CLI interfaces."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/forge.py"


def snapshot(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts}


class ForgeInstallSmoke(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.project = self.base / "project with spaces"
        self.project.mkdir()
        self.home = self.base / "home"
        self.home.mkdir()
        self.gemini = self.home / ".gemini"
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.agy = self.bin / "agy"
        self.codex = self.bin / "codex"
        self.agy.write_text("""#!/usr/bin/env python3
import json, os, pathlib, sys
if sys.argv[1:] == ['--help']:
    print('--model --effort --mode --dangerously-skip-permissions -i')
elif sys.argv[1:] == ['models']:
    print('unavailable' if os.environ.get('MOCK_MODEL_MISSING') else 'gemini-4-neon-high')
else:
    pathlib.Path(os.environ['FORGE_ARGV_LOG']).write_text(json.dumps({'args':sys.argv[1:],'cwd':os.getcwd()}))
""")
        self.codex.write_text("""#!/usr/bin/env python3
import sys
if sys.argv[-1:] == ['--help']:
    print('--dangerously-bypass-approvals-and-sandbox --output-schema --json')
elif sys.argv[1:] == ['login', 'status']:
    print('Logged in (fixture)')
else:
    sys.exit(7)
""")
        self.agy.chmod(0o755)
        self.codex.chmod(0o755)
        self.env = {**os.environ, "HOME": str(self.home), "FORGE_ARGV_LOG": str(self.base / "argv.json")}

    def run_cli(self, command, *extra, script=SCRIPT, code=0, env=None):
        result = subprocess.run([sys.executable, str(script), command, "--project", str(self.project),
                                 "--gemini-dir", str(self.gemini), "--agy-bin", str(self.agy),
                                 "--codex-bin", str(self.codex), *extra], capture_output=True,
                                text=True, timeout=25, env=env or self.env)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return json.loads(result.stdout or result.stderr) if command != "start" else result

    def installed_script(self):
        return self.project / ".agents/skills/maverick-forge/scripts/forge.py"

    def test_install_repeat_and_merge(self):
        (self.project / "AGENTS.md").write_text("Keep the user's existing conventions.\n")
        (self.project / ".agents").mkdir()
        config = self.project / ".agents/mcp_config.json"
        config.write_text(json.dumps({"mcpServers": {"existing": {"command": "keep"}}, "other": 42}))
        settings = self.gemini / "antigravity-cli/settings.json"
        settings.parent.mkdir(parents=True)
        settings.write_text(json.dumps({"theme": "dark", "permissions": {"deny": ["keep-explicit-rule"]}}))
        settings.chmod(0o600)
        result = self.run_cli("install")
        self.assertEqual(result["status"], "installed")
        self.assertFalse(result["project_knowledge_ready"])
        self.assertEqual(result["runtime"], "NOT_TESTED")
        self.assertIn("Keep the user's existing conventions.", (self.project / "AGENTS.md").read_text())
        current = json.loads(config.read_text())
        self.assertEqual(current["mcpServers"]["existing"], {"command": "keep"})
        self.assertEqual(current["other"], 42)
        forge = current["mcpServers"]["maverick-forge"]
        self.assertEqual(forge["tools"]["forge_dispatch"]["background"], "always")
        self.assertEqual(forge["tools"]["forge_resume"]["background"], "always")
        self.assertEqual(forge["timeoutSeconds"], -1)
        current_settings = json.loads(settings.read_text())
        self.assertEqual(current_settings["theme"], "dark")
        self.assertEqual(current_settings["permissions"], {"deny": ["keep-explicit-rule"]})
        self.assertFalse(current_settings["enableTerminalSandbox"])
        self.assertTrue(current_settings["allowNonWorkspaceAccess"])
        self.assertEqual(settings.stat().st_mode & 0o777, 0o600)
        before = snapshot(self.base)
        self.assertEqual(self.run_cli("install")["changed"], [])
        self.assertEqual(snapshot(self.base), before)

    def test_legacy_migration_keeps_actual_personality_and_memory(self):
        (self.project / "AGENTS.md").write_text("Original project conventions.\n")
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/maverick.py"), "init", "--project", str(self.project)],
                              text=True, capture_output=True, timeout=15)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        old_persona = self.project / ".agents/skills/maverick/references/personas/hacker.md"
        old_persona.write_text(old_persona.read_text() + "\nMy explicit preference: explain this project in plain words.\n")
        preferences = self.project / ".maverick/preferences.json"
        preferences.write_text('{"rebel":{"challenge":"Question invented limits."}}\n')
        state = self.project / ".maverick/STATE.md"
        state.write_text("Keep this active experiment, checkpoint path and task ID.\n")
        protected_paths = [state, preferences, self.project / ".maverick/PROJECT.md",
                           self.project / ".maverick/knowledge/domain.md", self.project / ".maverick/contributions.jsonl",
                           self.project / ".codex/config.toml"]
        before = {p: p.read_bytes() for p in protected_paths}
        result = self.run_cli("install")
        self.assertIn("personas/hacker.md", result["migrated_personal_edits"])
        new_persona = self.project / ".agents/skills/maverick-forge/personas/hacker.md"
        self.assertEqual(new_persona.read_bytes(), old_persona.read_bytes())
        self.assertEqual({p: p.read_bytes() for p in protected_paths}, before)
        root_rules = (self.project / "AGENTS.md").read_text()
        self.assertNotIn("<!-- maverick-codex:start -->", root_rules)
        self.assertIn("Original project conventions.", root_rules)
        self.assertIn("AGY is the only Maverick controller", root_rules)
        self.assertTrue((self.project / ".maverick/forge/legacy-AGENTS.md").exists())
        self.run_cli("update")
        self.assertEqual(new_persona.read_bytes(), old_persona.read_bytes())

    def test_local_edits_preserved_with_incoming_candidate(self):
        self.run_cli("install")
        target = self.project / ".agents/skills/maverick-forge"
        persona = target / "personas/rebel.md"
        skill = target / "SKILL.md"
        persona.write_text(persona.read_text() + "\nExplicit local personality adjustment.\n")
        skill.write_text(skill.read_text() + "\nProject-specific invocation note.\n")
        before = {p: p.read_bytes() for p in (persona, skill)}
        result = self.run_cli("update")
        self.assertEqual(set(result["preserved_local_edits"]), {"SKILL.md", "personas/rebel.md"})
        self.assertEqual({p: p.read_bytes() for p in before}, before)
        candidate = self.project / ".maverick/forge/incoming/personas/rebel.md"
        self.assertEqual(candidate.read_bytes(), (ROOT / "personas/rebel.md").read_bytes())
        old_hashes = json.loads((self.project / ".maverick/forge-manifest.json").read_text())["managed_files"]
        self.run_cli("install", script=self.installed_script())
        new_hashes = json.loads((self.project / ".maverick/forge-manifest.json").read_text())["managed_files"]
        self.assertEqual(old_hashes["personas/rebel.md"], new_hashes["personas/rebel.md"])

    def test_download_source_can_disappear_and_launcher_pins_model(self):
        source = self.base / "download-source"
        shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.run_cli("install", script=source / "scripts/forge.py")
        shutil.rmtree(source)
        static = self.run_cli("doctor", "--static", script=self.installed_script())
        self.assertTrue(static["installed"])
        self.assertTrue(static["static_checks"]["mcp_handshake"])
        self.assertIsNone(static["runtime_ready"])
        self.assertEqual(static["live_roundtrip"], "NOT_TESTED_BY_DOCTOR")
        pending = self.run_cli("doctor", script=self.installed_script(), code=2)
        self.assertTrue(pending["runtime_ready"])
        self.assertFalse(pending["project_knowledge_ready"])
        for name in ("PROJECT.md", "knowledge/domain.md"):
            (self.project / ".maverick" / name).write_text("# Test project\n\nStatus: READY\n\nEvidence: test fixture.\n")
        self.assertTrue(self.run_cli("doctor", script=self.installed_script())["runtime_ready"])
        launcher = self.project / ".maverick/forge/start"
        result = subprocess.run([str(launcher), "Inspect the next useful mechanism."], env=self.env,
                                text=True, capture_output=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        log = json.loads((self.base / "argv.json").read_text())
        self.assertEqual(log["cwd"], str(self.project))
        self.assertEqual(log["args"], ["--model", "gemini-4-neon-high", "--effort", "high", "--mode", "accept-edits",
                                      "--dangerously-skip-permissions", "-i", "/maverick-forge\nInspect the next useful mechanism."])
        rejected = subprocess.run([str(launcher), "--model", "different-model"], env=self.env,
                                  text=True, capture_output=True, timeout=5)
        self.assertNotEqual(rejected.returncode, 0)
        missing = {**self.env, "MOCK_MODEL_MISSING": "1"}
        (self.base / "argv.json").unlink()
        self.run_cli("start", script=self.installed_script(), env=missing, code=1)
        self.assertFalse((self.base / "argv.json").exists())

    def test_invalid_existing_config_does_not_partially_install(self):
        (self.project / ".agents").mkdir()
        (self.project / ".agents/mcp_config.json").write_text("{invalid-json")
        before = snapshot(self.base)
        self.run_cli("install", code=1)
        self.assertEqual(snapshot(self.base), before)

    def test_bootstrap_uses_project_directory_with_spaces(self):
        env = {**self.env, "FORGE_SOURCE": str(ROOT), "AGY_BIN": str(self.agy), "CODEX_BIN": str(self.codex)}
        result = subprocess.run(["bash", str(ROOT / "scripts/install.sh"), "--project", str(self.project),
                                 "--gemini-dir", str(self.gemini)], capture_output=True, text=True,
                                env=env, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.project / ".maverick/forge/start").is_file())

    def test_doctor_does_not_rewrite_saved_tasks(self):
        self.run_cli("install")
        run = self.project / ".maverick/forge/tasks/active-task/hacker/run.json"
        run.parent.mkdir(parents=True)
        run.write_text(json.dumps({"run_id": "fixture", "status": "running", "bridge_pid": -1, "pid": None}))
        before = snapshot(run.parent)
        self.run_cli("doctor", "--static", script=self.installed_script())
        self.assertEqual(snapshot(run.parent), before)

    def test_actual_home_and_runtime_binary_binding(self):
        self.run_cli("install")
        different_home = self.base / "unconfigured-home"
        different_home.mkdir()
        alternate = {**self.env, "HOME": str(different_home)}
        self.run_cli("start", env=alternate, code=1)
        self.assertFalse((self.base / "argv.json").exists())
        replacement = self.bin / "codex-replacement"
        shutil.copy2(self.codex, replacement)
        self.run_cli("start", "--codex-bin", str(replacement))
        config_path = self.project / ".agents/mcp_config.json"
        config = json.loads(config_path.read_text())
        self.assertEqual(config["mcpServers"]["maverick-forge"]["env"]["CODEX_BIN"], str(replacement))
        self.assertEqual(json.loads((self.project / ".maverick/forge-manifest.json").read_text())["codex_bin"], str(replacement))

        # A package-manager move must not leave a saved obsolete executable permanently binding the launcher.
        manifest_path = self.project / ".maverick/forge-manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest.update(agy_bin="/obsolete/agy", codex_bin="/obsolete/codex")
        manifest_path.write_text(json.dumps(manifest))
        config["mcpServers"]["maverick-forge"]["env"]["CODEX_BIN"] = "/obsolete/codex"
        config_path.write_text(json.dumps(config))
        env = {**self.env, "PATH": str(self.bin) + os.pathsep + self.env.get("PATH", "")}
        proc = subprocess.run([str(self.project / ".maverick/forge/start"), "Resume useful work."],
                              capture_output=True, text=True, env=env, timeout=25)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        actual = json.loads(config_path.read_text())["mcpServers"]["maverick-forge"]["env"]["CODEX_BIN"]
        self.assertEqual(actual, str(self.codex))


if __name__ == "__main__":
    unittest.main()

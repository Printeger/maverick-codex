#!/usr/bin/env python3
"""Install and launch the project-local Maverick Forge. Python 3.11+, stdlib only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile

VERSION = "0.1.0"
NAME = "maverick-forge"
MODEL = "gemini-4-neon-high"
ROLES = ("maverick", "rebel", "inventor", "hacker", "scientist", "producer")
TOOLS = ("forge_dispatch", "forge_resume", "forge_status", "forge_cancel",
         "forge_decide", "forge_record", "forge_report")
PERMISSIONS = {"agentMode": "accept-edits", "toolPermission": "always-proceed",
               "artifactReviewPolicy": "always-proceed", "enableTerminalSandbox": False,
               "allowNonWorkspaceAccess": True}
START, END = "<!-- maverick-forge:start -->", "<!-- maverick-forge:end -->"
OLD_START, OLD_END = "<!-- maverick-codex:start -->", "<!-- maverick-codex:end -->"
ROOT = Path(__file__).resolve().parent.parent


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def read_object(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: Path, data: bytes, executable=False) -> bool:
    if path.exists() and path.read_bytes() == data:
        if executable:
            path.chmod(path.stat().st_mode | 0o111)
        return False
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o644
    if executable:
        mode |= 0o111
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        temporary = Path(f.name)
        try:
            f.write(data)
            f.close()
            temporary.chmod(mode)
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)
    return True


def binary(name: str, configured=None):
    candidate = configured or os.environ.get(name.upper() + "_BIN")
    if candidate:
        found = shutil.which(os.path.expanduser(str(candidate)))
        if found:
            return found
    return shutil.which(name) or shutil.which(str(Path.home() / ".local/bin" / name))


def validate_explicit_binaries(args):
    for name in ("agy", "codex"):
        value = getattr(args, name + "_bin")
        if value and not shutil.which(os.path.expanduser(str(value))):
            raise ValueError(f"{name} executable not found: {value}")


def package_files() -> dict[str, bytes]:
    skill = ROOT / "skills/maverick-forge/SKILL.md"
    if not skill.exists():
        skill = ROOT / "SKILL.md"
    required = [skill, ROOT / "forge/server.py", ROOT / "forge/runtime.py",
                ROOT / "forge/report.schema.json", ROOT / "scripts/contributions.py"]
    required.extend(ROOT / f"personas/{role}.md" for role in ROLES)
    required.append(ROOT / "knowledge/INDEX.md")
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise ValueError("Incomplete Forge source package: " + ", ".join(missing))
    files = {"SKILL.md": skill.read_bytes()}
    if (ROOT / "THIRD_PARTY_NOTICES.md").is_file():
        files["THIRD_PARTY_NOTICES.md"] = (ROOT / "THIRD_PARTY_NOTICES.md").read_bytes()
    for directory in ("personas", "knowledge", "forge"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and path.suffix in {".md", ".py", ".json"}:
                files[str(path.relative_to(ROOT))] = path.read_bytes()
    for name in ("forge.py", "contributions.py", "install.sh"):
        files[f"scripts/{name}"] = (ROOT / "scripts" / name).read_bytes()
    agents = skill.parent / "agents"
    if agents.is_dir():
        for path in sorted(agents.iterdir()):
            if path.is_file():
                files[f"agents/{path.name}"] = path.read_bytes()
    return files


def marker_span(text: str, start: str, end: str):
    if start not in text and end not in text:
        return None
    if text.count(start) != 1 or text.count(end) != 1 or text.index(end) < text.index(start):
        raise ValueError(f"Incomplete or duplicate instruction markers: {start}")
    return text.index(start), text.index(end) + len(end)


def guidance(kind: str) -> str:
    shared = """## Maverick Forge for this project

AGY is the only Maverick controller. Read `.agents/skills/maverick-forge/SKILL.md`,
the full applicable personality in `.agents/skills/maverick-forge/personas/`,
`.maverick/PROJECT.md`, `.maverick/STATE.md` and `.maverick/preferences.json`.
Use project knowledge on demand; Inventor also uses the cross-disciplinary atlas at
`.agents/skills/maverick-forge/knowledge/INDEX.md`.

Invoking Forge means all six real personalities participate in each user-level task:
five independent Codex initial judgments, then Maverick's synthesis. Follow-up is
targeted, with the same persona and saved Codex session. There is no mode selector.
Only actual returned work counts; a controller perspective is not another participant.
Forge run state under `.maverick/forge/tasks/` and the contribution ledger preserve
history across sessions. Old STATE wording is history, not the current protocol.

A Codex process launched by Forge keeps the persona injected by its controller.
It is a worker even though `codex exec` creates a top-level CLI session. It must not
adopt Maverick, re-run the legacy root protocol, dispatch another team or write the
central contribution ledger. Report requests for other perspectives to AGY.
The old Maverick installation remains available only when explicitly requested;
its root scheduling instructions do not govern a Forge worker.

All Forge processes use the user's authorized full operating-system permissions.
An initial independent judgment is a task scope, not an operating-system sandbox.
Do not invent user approvals, reviewer-proof gates or a new process department.
Preserve explicit user boundaries and observed physical constraints. Historical
implementation assumptions are open to challenge. AGY decides changes to core
mechanisms, objectives or effective operating ranges; ordinary implementation is
autonomous. Select a worthwhile mechanism, then make its experiment small. Do not
shrink an open research goal into a parameter tweak merely to minimize the diff.
Personality changes require an explicit user update; project facts stay separate.
"""
    if kind == "GEMINI.md":
        shared += """
You are Maverick: use the complete `personas/maverick.md`, including its voice and
tradeoffs. The fixed controller is Gemini 4 Neon high. Delegate through the Forge
MCP tools; dispatch/resume return in the background and wake you when complete.
Do useful independent work or yield while waiting. Do not poll in a model loop.
At task completion report real role contributions and the most valuable change in
understanding. Use `forge_report` and preserve a compact STATE handoff.
"""
    return START + "\n" + shared + END


def merge_guidance(text: str, kind: str):
    legacy = None
    span = marker_span(text, OLD_START, OLD_END)
    if span:
        legacy = text[span[0]:span[1]]
        text = text[:span[0]] + text[span[1]:]
    span = marker_span(text, START, END)
    block = guidance(kind)
    if span:
        return text[:span[0]] + block + text[span[1]:], legacy
    return text.rstrip() + ("\n\n" if text.strip() else "") + block + "\n", legacy


def mcp_entry(project: Path, target: Path, codex):
    env = {"PYTHONUNBUFFERED": "1", "MAVERICK_PROJECT": str(project)}
    if codex:
        env["CODEX_BIN"] = codex
    return {"command": sys.executable, "args": [str(target / "forge/server.py")],
            "cwd": str(project), "env": env, "timeoutSeconds": -1,
            "tools": {tool: {"eager": True, "background": "always" if tool in
                       {"forge_dispatch", "forge_resume"} else "off"} for tool in TOOLS}}


def install(args):
    project = args.project.resolve()
    if not project.is_dir():
        raise ValueError(f"Project directory does not exist: {project}")
    target = project / ".agents/skills/maverick-forge"
    manifest_path = project / ".maverick/forge-manifest.json"
    old = read_object(manifest_path)
    if old and old.get("format") != 1:
        raise ValueError("Unsupported Forge installation format; no files changed.")
    managed = old.get("managed_files", {})
    if not isinstance(managed, dict):
        raise ValueError("Invalid Forge managed_files; no files changed.")
    gemini = Path(args.gemini_dir or old.get("gemini_dir") or Path.home() / ".gemini").expanduser().resolve()
    agy = binary("agy", args.agy_bin or old.get("agy_bin"))
    codex = binary("codex", args.codex_bin or old.get("codex_bin"))
    validate_explicit_binaries(args)
    files = package_files()
    writes, conflicts, migrated = {}, [], []
    hashes = dict(managed)
    for name, incoming in files.items():
        path = target / name
        current = path.read_bytes() if path.exists() else None
        source_hash = digest(incoming)
        legacy = project / ".agents/skills/maverick/references" / name
        if current is None and name.startswith(("personas/", "knowledge/")) and legacy.is_file():
            writes[path] = legacy.read_bytes()
            hashes[name] = source_hash
            if writes[path] != incoming:
                migrated.append(name)
            continue
        if current is None or current == incoming or digest(current) == managed.get(name):
            writes[path] = incoming
            # Re-running the installed copy must not adopt hand-edited files as defaults.
            hashes[name] = managed.get(name, source_hash) if ROOT == target else source_hash
        else:
            conflicts.append(name)
            writes[project / ".maverick/forge/incoming" / name] = incoming

    for kind in ("AGENTS.md", "GEMINI.md"):
        path = project / kind
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        updated, legacy = merge_guidance(text, kind)
        writes[path] = updated.encode()
        backup = project / f".maverick/forge/legacy-{kind}"
        if legacy and not backup.exists():
            writes[backup] = (legacy + "\n").encode()

    mcp_path = project / ".agents/mcp_config.json"
    mcp = read_object(mcp_path)
    servers = mcp.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError(f"mcpServers must be an object: {mcp_path}")
    servers[NAME] = mcp_entry(project, target, codex)
    writes[mcp_path] = json_text(mcp).encode()
    settings_path = gemini / "antigravity-cli/settings.json"
    settings = read_object(settings_path)
    settings.update(PERMISSIONS)
    writes[settings_path] = json_text(settings).encode()

    memory = {
        "PROJECT.md": f"# {project.name}\n\nStatus: PENDING\n\n## Goal and boundaries\nRead the user's goal and actual project sources.\n\n## Source map\nRecord real entry points, useful commands and known limits.\n",
        "STATE.md": "# Current state\n\nForge files installed. Project adaptation and real six-person execution remain.\n\n## Current task\nNo task started. Preserve the task ID, returned roles, chosen route and next step here.\n",
        "preferences.json": "{}\n", "contributions.jsonl": "",
        "knowledge/INDEX.md": "# Project knowledge\n\n- [Domain background](domain.md)\n- Cross-disciplinary atlas: `.agents/skills/maverick-forge/knowledge/INDEX.md`.\n\nKeep sourced project facts separate from reusable personalities. Read only relevant cards.\n",
        "knowledge/domain.md": "# Domain background\n\nStatus: PENDING\n\n## Concepts and mechanisms\nFill from actual repository files and verified primary sources.\n\n## Evidence and gaps\nRecord source paths and unknowns that affect the next decision.\n",
    }
    for name, content in memory.items():
        path = project / ".maverick" / name
        if not path.exists():
            writes[path] = content.encode()

    launcher = project / ".maverick/forge/start"
    command = [sys.executable, str(target / "scripts/forge.py"), "start", "--project", str(project)]
    writes[launcher] = ("#!/bin/sh\nexec " + shlex.join(command) + ' "$@"\n').encode()
    writes[manifest_path] = json_text({"format": 1, "product": "Maverick Forge", "version": VERSION,
        "controller_model": MODEL, "controller_effort": "high", "gemini_dir": str(gemini),
        "agy_bin": agy, "codex_bin": codex, "managed_files": hashes}).encode()

    # Validate JSON and marker merges before writing anything; preserve unrelated text/settings.
    changed = []
    for path, data in writes.items():
        if write(path, data, executable=path == launcher):
            changed.append(str(path))
    return {"status": "installed", "version": VERSION, "project": str(project), "changed": changed,
            "preserved_local_edits": conflicts, "migrated_personal_edits": migrated,
            "incoming_candidates": str(project / ".maverick/forge/incoming") if conflicts else None,
            "runtime": "NOT_TESTED", "project_knowledge_ready": knowledge_ready(project),
            "executables": {"agy": agy, "codex": codex}, "settings_path": str(settings_path),
            "next": f"Run {shlex.quote(str(launcher))}; use doctor to check CLI readiness. "
                    "If AGY is missing: curl -fsSL https://antigravity.google/cli/install.sh | bash. "
                    "Install/login to Codex separately if it is missing. No model fallback is configured."}


def knowledge_ready(project: Path) -> bool:
    return all((path := project / ".maverick" / name).is_file() and
               re.search(r"(?mi)^Status:\s*READY\s*$", path.read_text(encoding="utf-8"))
               for name in ("PROJECT.md", "knowledge/domain.md"))


def capture(command, *, cwd=None, input=None, timeout=20, env=None):
    try:
        result = subprocess.run(command, cwd=cwd, input=input, stdin=None if input is not None else subprocess.DEVNULL,
                                text=True, capture_output=True, timeout=timeout, env=env)
        return result.returncode, result.stdout + result.stderr
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, str(exc)


def check_cli(agy, codex, project):
    checks, notes = {}, []
    if agy:
        code, help_text = capture([agy, "--help"])
        checks["agy_interface"] = code == 0 and all(flag in help_text for flag in
            ("--model", "--effort", "--mode", "--dangerously-skip-permissions"))
        code, model_text = capture([agy, "models"], cwd=project)
        checks["neon_available"] = code == 0 and bool(re.search(r"(?<![\w-])" + re.escape(MODEL) + r"(?![\w-])", model_text))
        if not checks["neon_available"]:
            notes.append("AGY did not confirm gemini-4-neon-high. Run agy models and complete login; no fallback was selected.")
    else:
        checks.update(agy_interface=False, neon_available=False)
        notes.append("AGY not found. Install from https://antigravity.google/cli/install.sh and complete its login.")
    if codex:
        code, help_text = capture([codex, "exec", "--help"], cwd=project)
        checks["codex_interface"] = code == 0 and all(flag in help_text for flag in
            ("--dangerously-bypass-approvals-and-sandbox", "--output-schema", "--json"))
        code, resume_text = capture([codex, "exec", "resume", "--help"], cwd=project)
        checks["codex_resume"] = code == 0 and all(flag in resume_text for flag in
            ("--dangerously-bypass-approvals-and-sandbox", "--output-schema", "--json"))
        code, _ = capture([codex, "login", "status"], cwd=project)
        checks["codex_login"] = code == 0
        if not checks["codex_login"]:
            notes.append("Codex login is not confirmed. Run codex login before dispatching a worker.")
    else:
        checks.update(codex_interface=False, codex_resume=False, codex_login=False)
        notes.append("Codex executable not found. Install Codex CLI and run codex login.")
    return checks, notes


def doctor(args):
    project = args.project.resolve()
    target = project / ".agents/skills/maverick-forge"
    info = read_object(project / ".maverick/forge-manifest.json")
    gemini = Path(args.gemini_dir or info.get("gemini_dir") or Path.home() / ".gemini").expanduser()
    agy = binary("agy", args.agy_bin or info.get("agy_bin"))
    codex = binary("codex", args.codex_bin or info.get("codex_bin"))
    required = ["SKILL.md", "forge/server.py", "forge/runtime.py", "forge/report.schema.json",
                "scripts/forge.py", "scripts/contributions.py", "knowledge/INDEX.md"]
    required += [f"personas/{role}.md" for role in ROLES]
    missing = [name for name in required if not (target / name).is_file()]
    mcp = read_object(project / ".agents/mcp_config.json").get("mcpServers", {}).get(NAME, {})
    settings = read_object(gemini / "antigravity-cli/settings.json")
    expected = mcp_entry(project, target, codex)
    config_ok = all(mcp.get(key) == expected[key] for key in ("command", "args", "cwd", "timeoutSeconds", "tools"))
    config_ok = config_ok and all(mcp.get("env", {}).get(key) == value for key, value in
                                 {"PYTHONUNBUFFERED": "1", "MAVERICK_PROJECT": str(project)}.items())
    configured_codex = mcp.get("env", {}).get("CODEX_BIN")
    config_ok = config_ok and (not configured_codex or configured_codex == codex)
    permissions_ok = all(settings.get(key) == value for key, value in PERMISSIONS.items())
    static = {"package_complete": bool(info) and not missing, "mcp_config": config_ok,
              "full_permissions": permissions_ok}
    notes = []
    if not missing and mcp:
        requests = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params":
                {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "forge-doctor", "version": VERSION}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        ]
        handshake_env = {**os.environ, **mcp.get("env", {})}
        # A protocol check must not recover or rewrite another bridge's active task state.
        handshake_env.pop("MAVERICK_PROJECT", None)
        code, output = capture([sys.executable, str(target / "forge/server.py")], cwd=project,
                               input="".join(json.dumps(item) + "\n" for item in requests), timeout=10,
                               env=handshake_env)
        try:
            replies = [json.loads(line) for line in output.splitlines() if line.startswith("{")]
            listed = next(item["result"]["tools"] for item in replies if item.get("id") == 2)
            static["mcp_handshake"] = code == 0 and set(TOOLS) <= {item["name"] for item in listed}
        except (ValueError, KeyError, StopIteration, TypeError):
            static["mcp_handshake"] = False
        if not static["mcp_handshake"]:
            notes.append("MCP handshake failed: " + output[-700:])
    else:
        static["mcp_handshake"] = False
    runtime = {}
    if not args.static:
        runtime, runtime_notes = check_cli(agy, codex, project)
        notes += runtime_notes
        runtime["agy_settings_location"] = gemini.resolve() == (Path.home() / ".gemini").resolve()
        if not runtime["agy_settings_location"]:
            notes.append("--gemini-dir selects a configuration file for installation/checks; AGY actually reads ~/.gemini. Use the same HOME when launching.")
    return {"version": VERSION, "installed": all(static.values()), "static_checks": static,
            "missing_files": missing, "project_knowledge_ready": bool(knowledge_ready(project)),
            "runtime_ready": all(runtime.values()) if runtime else None, "runtime_checks": runtime,
            "live_roundtrip": "NOT_TESTED_BY_DOCTOR", "controller_model": MODEL,
            "codex_model": "gpt-6.2-sol", "notes": notes}


def start(args):
    project = args.project.resolve()
    info = read_object(project / ".maverick/forge-manifest.json")
    if not info:
        raise ValueError("Forge is not installed in this project. Run install first.")
    validate_explicit_binaries(args)
    agy = binary("agy", args.agy_bin or info.get("agy_bin"))
    codex = binary("codex", args.codex_bin or info.get("codex_bin"))
    checks, notes = check_cli(agy, codex, project)
    if not all(checks.values()):
        raise ValueError("Runtime is not ready: " + "; ".join(notes or [key for key, ok in checks.items() if not ok]))
    gemini = Path(args.gemini_dir or info["gemini_dir"])
    if gemini.resolve() != (Path.home() / ".gemini").resolve():
        raise ValueError("AGY reads ~/.gemini. This installation used a different --gemini-dir; reinstall for the current HOME or launch with the matching HOME. No unsupported AGY configuration override was invented.")
    settings_path = gemini / "antigravity-cli/settings.json"
    settings = read_object(settings_path)
    settings.update(PERMISSIONS)
    write(settings_path, json_text(settings).encode())
    # Refresh only this bridge's executable after a CLI move or an explicit override.
    mcp_path = project / ".agents/mcp_config.json"
    mcp = read_object(mcp_path)
    server = mcp.get("mcpServers", {}).get(NAME)
    if not isinstance(server, dict):
        raise ValueError("Forge MCP entry is missing. Run install again.")
    server.setdefault("env", {})["CODEX_BIN"] = codex
    write(mcp_path, json_text(mcp).encode())
    info.update(agy_bin=agy, codex_bin=codex)
    write(project / ".maverick/forge-manifest.json", json_text(info).encode())
    prompt = "/maverick-forge"
    if args.prompt:
        prompt += "\n" + args.prompt
    command = [agy, "--model", MODEL, "--effort", "high", "--mode", "accept-edits",
               "--dangerously-skip-permissions", "-i", prompt]
    return subprocess.call(command, cwd=project)


def main():
    if sys.version_info < (3, 11):
        raise SystemExit("Maverick Forge requires Python 3.11 or newer.")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("install", "update", "doctor", "start"):
        p = sub.add_parser(name, help="install/update from this source package" if name in {"install", "update"} else None)
        p.add_argument("--project", type=Path, default=Path.cwd())
        p.add_argument("--gemini-dir", type=Path, help="AGY settings directory (default: ~/.gemini)")
        p.add_argument("--agy-bin")
        p.add_argument("--codex-bin")
        if name == "doctor":
            p.add_argument("--static", action="store_true", help="skip account/model availability commands")
        if name == "start":
            p.add_argument("prompt", nargs="?", help="initial task; model/permission flags remain fixed")
    args = parser.parse_args()
    try:
        if args.command == "start":
            return start(args)
        result = doctor(args) if args.command == "doctor" else install(args)
        print(json_text(result), end="")
        if args.command == "doctor":
            return 0 if result["installed"] and (args.static or
                         (result["runtime_ready"] and result["project_knowledge_ready"])) else 2
        return 0
    except (OSError, ValueError, TypeError) as exc:
        print(json_text({"error": str(exc)}), file=sys.stderr, end="")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

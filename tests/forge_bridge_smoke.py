#!/usr/bin/env python3
"""Exercise subprocess/session wiring without spending model tokens or modifying a real project."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import textwrap
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from forge.runtime import ForgeRuntime, PERSONAS, read_json, write_json


def fixture(root: Path) -> tuple[Path, Path]:
    project = root / "project with spaces"
    project.mkdir()
    (project / "input.txt").write_text("A real fixture to inspect.\n")
    codex = root / "fake codex"
    codex.write_text(f"#!{sys.executable}\n" + textwrap.dedent(r'''
        import json, pathlib, re, sys, time, uuid
        if "--help" in sys.argv:
            print("--dangerously-bypass-hook-trust")
            raise SystemExit(0)
        prompt = sys.stdin.read()
        instruction = prompt.split("## 本次委派\n", 1)[-1]
        args = sys.argv[1:]
        persona = re.search(r"# Maverick Forge · (\w+)", prompt).group(1).lower()
        session = args[-2] if "resume" in args else "session-" + uuid.uuid4().hex
        with pathlib.Path("calls.jsonl").open("a") as target:
            target.write(json.dumps({"argv": args, "prompt": prompt, "persona": persona, "session": session}) + "\n")
        if "MOCK_NO_SESSION" not in instruction:
            print(json.dumps({"type": "thread.started", "thread_id": session}), flush=True)
        if "MOCK_WAIT" in instruction:
            time.sleep(20)
        report = {"status": "completed", "summary": persona + " returned a concrete judgment",
                  "next_step": "Try the discriminating experiment.", "evidence": ["input.txt"],
                  "files_changed": [], "commands_run": ["read input.txt"]}
        path = pathlib.Path(args[args.index("-o") + 1])
        path.write_text("not json" if "MOCK_BAD_REPORT" in instruction else json.dumps(report))
        print(json.dumps({"type": "turn.completed"}), flush=True)
        raise SystemExit(2 if "MOCK_FAIL" in instruction else 0)
    '''))
    codex.chmod(0o755)
    return project, codex


def reject(function, *args, **kwargs):
    try:
        function(*args, **kwargs)
    except ValueError:
        return
    raise AssertionError("Expected a specific invalid transition to be rejected.")


def test_lifecycle(root: Path):
    project, codex = fixture(root)
    runtime = ForgeRuntime(project, str(codex))
    reject(runtime.decide, str(project), "task", "Choose a route too early")
    reject(runtime.dispatch, str(project), "../escape", "rebel", "Question this")
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(runtime.dispatch, str(project), "task", role, "Inspect the actual problem.")
                   for role in PERSONAS]
        results = [future.result(timeout=20) for future in futures]
    assert all(result["initial_complete"] for result in results), results
    assert len({result["session_id"] for result in results}) == 5
    assert all(result["observed_model"] is None for result in results)
    calls = [json.loads(line) for line in (project / "calls.jsonl").read_text().splitlines()]
    for call in calls:
        assert "--dangerously-bypass-approvals-and-sandbox" in call["argv"]
        assert "--dangerously-bypass-hook-trust" in call["argv"]
        assert call["argv"][call["argv"].index("-m") + 1] == "gpt-6.2-sol"
        assert (ROOT / "personas" / f"{call['persona']}.md").read_text() in call["prompt"]
        assert "不要运行旧根协调流程" in call["prompt"]
    inventor = next(call for call in calls if call["persona"] == "inventor")
    assert (ROOT / "knowledge/INDEX.md").read_text() in inventor["prompt"]
    reject(runtime.dispatch, str(project), "task", "rebel", "Duplicate")
    state = runtime.status(str(project), "task")
    assert state["missing_personas"] == ["maverick"]
    runtime.decide(str(project), "task", "Use the alternative mechanism; compare the two actual predictions.")
    assert runtime.report(str(project), "task")["initial_complete"]
    rebel = next(result for result in results if result["persona"] == "rebel")
    initial_id = f"forge-initial-rebel-{rebel['run_id'][:8]}"
    revised = runtime.record(str(project), "task", "rebel", "direction", "Questioned the inherited constraint",
                             "The selected route removes it", [rebel["report_path"]], 2, event_id=initial_id)
    assert revised["revision"] and runtime.report(str(project), "task")["initial_complete"]
    hacker = next(result for result in results if result["persona"] == "hacker")
    continued = runtime.resume(hacker["run_id"], "Implement the chosen local experiment.")
    assert continued["session_id"] == hacker["session_id"] and continued["round"] == 2
    last = json.loads((project / "calls.jsonl").read_text().splitlines()[-1])
    assert "resume" in last["argv"] and "-C" not in last["argv"]
    assert last["argv"][-2] == hacker["session_id"]
    runtime.record(str(project), "task", "hacker", "implementation", "Built the actual experiment",
                   "The fixture completed", [continued["report_path"]], 2)
    rendered = runtime.report(str(project), "task")
    assert "2 · 实质" in rendered["markdown"] and "6/6" in rendered["markdown"]
    runtime.codex_bin = str(root / "missing-codex")
    failed = runtime.resume(hacker["run_id"], "Continue after a missing executable")
    assert failed["status"] == "failed" and failed["report"] is None and failed["observed_model"] is None
    runtime.close()


def test_failure_cancel_recovery(root: Path):
    project, codex = fixture(root)
    runtime = ForgeRuntime(project, str(codex))
    for token in ("MOCK_FAIL", "MOCK_BAD_REPORT", "MOCK_NO_SESSION"):
        result = runtime.dispatch(str(project), token, "rebel", token)
        assert result["status"] == "failed" and not result["initial_complete"], result
        reject(runtime.record, str(project), token, "rebel", "direction", "A claim", "A claim", ["input.txt"], 3)
        retry = runtime.resume(result["run_id"], "Now return a complete independent judgment")
        assert retry["initial_complete"]
        if result["session_id"]:
            assert retry["session_id"] == result["session_id"]
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending = [pool.submit(runtime.dispatch, str(project), "cancel", role, "MOCK_WAIT")
                   for role in ("rebel", "inventor", "hacker")]
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            workers = runtime.status(str(project), "cancel")["workers"]
            if len(workers) == 3 and sum(x["status"] == "running" for x in workers.values()) == 2:
                break
            time.sleep(0.02)
        else:
            raise AssertionError("Expected two running workers and one queued worker.")
        queued = next(worker for worker in workers.values() if worker["status"] == "queued")
        runtime.cancel(queued["run_id"])
        for worker in workers.values():
            if worker["run_id"] != queued["run_id"]:
                runtime.cancel(worker["run_id"])
        assert all(future.result(timeout=8)["status"] == "cancelled" for future in pending)
        calls = [json.loads(line) for line in (project / "calls.jsonl").read_text().splitlines()]
        assert not any(call["persona"] == queued["persona"] and "MOCK_WAIT" in call["prompt"] for call in calls)
    recover_path = project / ".maverick/forge/tasks/MOCK_FAIL/rebel/run.json"
    saved = read_json(recover_path)
    saved.update(status="queued", bridge_pid=None, pid=None)
    write_json(recover_path, saved)
    restored = ForgeRuntime(project, str(codex))
    assert restored.status(str(project), "MOCK_FAIL")["workers"]["rebel"]["status"] == "interrupted"
    assert restored.resume(saved["run_id"], "Continue the same recovered persona")["status"] == "completed"
    restored.close()
    runtime.close()


def test_mcp(root: Path):
    project, codex = fixture(root)
    process = subprocess.Popen([sys.executable, str(ROOT / "forge/server.py"), "--project", str(project)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, env={**os.environ, "CODEX_BIN": str(codex)})
    def send(number, method, params):
        process.stdin.write(json.dumps({"jsonrpc": "2.0", "id": number, "method": method, "params": params}) + "\n")
        process.stdin.flush()
    send(1, "initialize", {"protocolVersion": "2025-03-26"})
    assert json.loads(process.stdout.readline())["result"]["serverInfo"]["name"] == "maverick-forge"
    send(2, "tools/list", {})
    assert len(json.loads(process.stdout.readline())["result"]["tools"]) == 7
    for number, role in enumerate(("rebel", "inventor"), 3):
        send(number, "tools/call", {"name": "forge_dispatch", "arguments": {
            "project": str(project), "task_id": "mcp", "persona": role, "prompt": "Inspect the evidence."}})
    replies = [json.loads(process.stdout.readline()) for _ in range(2)]
    assert {reply["id"] for reply in replies} == {3, 4}
    assert all(not reply["result"]["isError"] for reply in replies)
    assert all(json.loads(reply["result"]["content"][0]["text"])["initial_complete"] for reply in replies)
    send(5, "tools/call", {"name": "forge_dispatch", "arguments": {
        "project": str(project), "task_id": "mcp", "persona": "producer", "prompt": "MOCK_WAIT"}})
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        calls = [json.loads(line) for line in (project / "calls.jsonl").read_text().splitlines()]
        if any(call["persona"] == "producer" for call in calls):
            break
        time.sleep(0.02)
    else:
        raise AssertionError("MCP worker did not start before cancellation check.")
    process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/cancelled",
                                   "params": {"requestId": 5, "reason": "User cancelled the background call"}}) + "\n")
    process.stdin.flush()
    cancelled = json.loads(process.stdout.readline())
    assert cancelled["id"] == 5
    assert json.loads(cancelled["result"]["content"][0]["text"])["status"] == "cancelled"
    process.stdin.close()
    assert process.wait(timeout=10) == 0, process.stderr.read()


def main():
    for test in (test_lifecycle, test_failure_cancel_recovery, test_mcp):
        with tempfile.TemporaryDirectory(prefix="forge-bridge-") as directory:
            test(Path(directory))
        print(f"PASS {test.__name__}")
    print("Bridge smoke checks passed; fake CLI only, no live model execution.")


if __name__ == "__main__":
    main()

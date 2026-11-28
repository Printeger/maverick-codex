"""A small, persistent bridge to real Codex CLI sessions; no model routing."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import threading
from datetime import datetime, timezone
import uuid

ROOT = Path(__file__).resolve().parent.parent
MODEL = "gpt-6.2-sol"
EFFORT = {"rebel": "high", "inventor": "high", "hacker": "medium",
          "scientist": "high", "producer": "medium"}
PERSONAS = tuple(EFFORT)
_spec = importlib.util.spec_from_file_location("forge_contributions", ROOT / "scripts/contributions.py")
ledger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ledger)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def nonempty(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def valid_report(value: dict) -> bool:
    required = {"status", "summary", "next_step", "evidence", "files_changed", "commands_run"}
    return (isinstance(value, dict) and set(value) == required
            and value["status"] in ("completed", "partial", "blocked", "failed")
            and nonempty(value["summary"]) and isinstance(value["next_step"], str)
            and all(isinstance(value[key], list) and all(nonempty(x) for x in value[key])
                    for key in ("evidence", "files_changed", "commands_run")))


class ForgeRuntime:
    def __init__(self, project: str | Path | None = None, codex_bin: str | None = None):
        project = project or os.environ.get("MAVERICK_PROJECT")
        self.project = Path(project).expanduser().resolve() if project else None
        self.codex_bin = codex_bin or os.environ.get("CODEX_BIN") or "codex"
        self.lock = threading.RLock()
        self.slots = threading.BoundedSemaphore(2)
        self.runs: dict[str, Path] = {}
        self.processes: dict[str, subprocess.Popen] = {}
        self.active: set[str] = set()
        self.cancelled: set[str] = set()
        self.closed = False
        self.hook_trust: bool | None = None
        if self.project:
            self._index(self.project)

    def _project(self, value: str | Path) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute() or not path.is_dir():
            raise ValueError("project must be an absolute path to an existing directory.")
        path = path.resolve()
        if self.project and path != self.project:
            raise ValueError(f"This MCP server is configured for {self.project}.")
        self._index(path)
        return path

    def _index(self, project: Path) -> None:
        with self.lock:
            for path in (project / ".maverick/forge/tasks").glob("*/*/run.json"):
                run = self._refresh(path)
                if run.get("run_id"):
                    self.runs[run["run_id"]] = path

    @staticmethod
    def _alive(pid) -> bool:
        if not isinstance(pid, int) or pid <= 0:
            return False
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def _refresh(self, path: Path) -> dict:
        run = read_json(path)
        if run.get("status") not in ("queued", "starting", "running", "lost_contact") or run.get("run_id") in self.active:
            return run
        if self._alive(run.get("bridge_pid")):
            return run  # Another live MCP process owns this run.
        if self._alive(run.get("pid")):
            run["status"] = "lost_contact"
            run["error"] = f"Previous bridge exited; Codex PID {run['pid']} is still present. Inspect that process; resume after it exits."
        else:
            run.update(status="interrupted", pid=None,
                       error="Previous bridge exited before returning. Use forge_resume to continue this persona.")
        write_json(path, run)
        return run

    def _task(self, project: Path, task_id: str) -> Path:
        if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}", task_id):
            raise ValueError("task_id must be 1–96 letters, digits, underscores, dots or hyphens; start with a letter/digit.")
        return project / ".maverick/forge/tasks" / task_id

    def _run(self, run_id: str) -> tuple[Path, dict]:
        if run_id not in self.runs and self.project:
            self._index(self.project)
        path = self.runs.get(run_id)
        if path is None:
            raise ValueError("Unknown run_id; use forge_status for this project's saved sessions.")
        return path, self._refresh(path)

    def _asset(self, project: Path, relative: str) -> Path:
        installed = project / ".agents/skills/maverick-forge" / relative
        return installed if installed.is_file() else ROOT / relative

    def _prompt(self, run: dict, instruction: str, initial: bool) -> str:
        project = Path(run["project"])
        persona = run["persona"]
        personality = self._asset(project, f"personas/{persona}.md").read_text(encoding="utf-8")
        preference_file = project / ".maverick/preferences.json"
        preferences = read_json(preference_file).get(persona, {}) if preference_file.exists() else {}
        scope = (
            "本轮只形成独立判断：阅读事实、代码和既有结果，给出你的观点，不修改项目、不启动训练。"
            "这限定本次任务范围，操作系统权限保持完整。不要假设 Maverick 已经选定方案。"
            if initial else
            "首轮已经综合。按本次委派自主完成实现、实验或诊断；只改分配范围，避免与其他执行者互相覆盖。"
        )
        atlas = ""
        if persona == "inventor":
            atlas_path = self._asset(project, "knowledge/INDEX.md")
            atlas = f"\n## 跨学科知识入口\n路径：{atlas_path}\n{atlas_path.read_text(encoding='utf-8')}\n"
        return f"""# Maverick Forge · {persona.capitalize()}

AGY 主对话是唯一 Maverick。当前真实 Codex 会话固定为 {persona.capitalize()}，
不是另一个主控。即使项目中有旧 Maverick skill 或根协议，也不要运行旧根协调流程、
召集团队、创建子 Agent、冒用其他人格或写贡献总账。需要其他视角时，把问题交给 AGY。
完整操作系统权限已由用户授权；这不改变你的固定人格与本次工作范围。

{scope}

保留用户明确边界及已观察到的物理事实。历史实现假设、上一轮自己加的门限与时序契约
都可以质疑，不自动当成不可改变的用户要求。先选值得验证的机制，再缩小实现；
不能把开放工程目标自行缩成一个参数微调。不要为假想审稿意见偷偷增加门限、
收窄算法有效区间或改掉核心机制；把此类路线变化及依据交给 AGY 决定。
普通实现细节自己完成。运行能改变当前判断的检查，已有证据够用就停止重复验证。

## 完整人格
{personality}

## 项目人格偏好
{json.dumps(preferences, ensure_ascii=False, indent=2)}

## 事实入口
项目：{project}
任务：{run['task_id']}
阅读存在的 .maverick/PROJECT.md、.maverick/STATE.md、.maverick/knowledge/INDEX.md，
再按任务需要读取领域材料和具体代码。人格偏好、项目事实和推测应分清。
{atlas}
## 本次委派
{instruction}

## 返回
只用要求的 JSON 结构返回。summary 写实际结论与理由；next_step 写最有用的下一步；
evidence 引用真正读过或产生的文件/命令结果，不能伪造。files_changed 和 commands_run
如实填写，没有就用空数组。completed 表示这次委派完成，不表示提案已经有效。
"""

    def _command(self, run: dict, result: Path) -> list[str]:
        executable = shutil.which(self.codex_bin)
        if not executable:
            raise ValueError(f"Codex executable not found: {self.codex_bin}")
        if self.hook_trust is None:
            help_result = subprocess.run([executable, "exec", "--help"], capture_output=True,
                                         text=True, timeout=15, check=False)
            self.hook_trust = "--dangerously-bypass-hook-trust" in help_result.stdout
        command = [executable, "exec"]
        if run.get("session_id"):
            command.append("resume")
        command += ["-m", MODEL, "-c", f'model_reasoning_effort="{EFFORT[run["persona"]]}"',
                    "--dangerously-bypass-approvals-and-sandbox"]
        if self.hook_trust:
            command.append("--dangerously-bypass-hook-trust")
        if not run.get("session_id"):
            command += ["--skip-git-repo-check", "-C", run["project"]]
        command += ["--output-schema", str(ROOT / "forge/report.schema.json"), "-o", str(result), "--json"]
        if run.get("session_id"):
            command += ["--all", run["session_id"]]
        command.append("-")
        return command

    def dispatch(self, project: str, task_id: str, persona: str, prompt: str, _on_start=None) -> dict:
        project_path = self._project(project)
        task = self._task(project_path, task_id)
        if persona not in PERSONAS or not nonempty(prompt):
            raise ValueError("Choose one of the five worker personas and supply a nonempty prompt.")
        path = task / persona / "run.json"
        with self.lock:
            if self.closed:
                raise ValueError("Bridge is shutting down.")
            if path.exists():
                raise ValueError(f"This persona already has a run. Use forge_resume: {read_json(path)['run_id']}")
            run = {"run_id": uuid.uuid4().hex, "project": str(project_path), "task_id": task_id,
                   "persona": persona, "session_id": None, "round": 0, "status": "starting",
                   "initial_complete": False, "initial_report": None, "created_at": now(),
                   "bridge_pid": os.getpid(),
                   "requested_model": MODEL, "requested_effort": EFFORT[persona],
                   "observed_model": None, "observed_effort": None}
            self.runs[run["run_id"]] = path
            self.active.add(run["run_id"])
            write_json(path, run)
        if _on_start is not None:
            _on_start(run["run_id"])
        return self._execute(path, run, prompt)

    def resume(self, run_id: str, prompt: str, _on_start=None) -> dict:
        if not nonempty(prompt):
            raise ValueError("prompt must be nonempty.")
        with self.lock:
            path, run = self._run(run_id)
            if self.closed or run_id in self.processes or run["status"] in ("queued", "starting", "running", "lost_contact"):
                raise ValueError("Run is active or its prior process lost contact; do not resume concurrently. Inspect forge_status.")
            run["status"] = "starting"
            run["bridge_pid"] = os.getpid()
            self.active.add(run_id)
            self.cancelled.discard(run_id)
            write_json(path, run)
        if _on_start is not None:
            _on_start(run_id)
        return self._execute(path, run, prompt)

    def _execute(self, path: Path, run: dict, instruction: str) -> dict:
        run_id = run["run_id"]
        project = Path(run["project"])
        task = self._task(project, run["task_id"])
        initial_scope = not (task / "decision.json").exists()
        run["round"] += 1
        round_dir = path.parent / f"round-{run['round']}"
        round_dir.mkdir(parents=True, exist_ok=False)
        result_path = round_dir / "report.json"
        run.update(status="queued", updated_at=now(), round_dir=str(round_dir), error=None,
                   report=None, report_path=None, exit_code=None, observed_model=None, observed_effort=None,
                   turn_failed=None,
                   operation="resume" if run.get("session_id") else "new_session")
        process = None
        acquired = False
        try:
            with self.lock:
                write_json(path, run)
            while not acquired:
                if run_id in self.cancelled or self.closed:
                    raise ValueError("Run was cancelled while queued.")
                acquired = self.slots.acquire(timeout=0.25)
            text = self._prompt(run, instruction, initial_scope)
            (round_dir / "prompt.md").write_text(text, encoding="utf-8")
            command = self._command(run, result_path)
            write_json(round_dir / "invocation.json", {"argv": command, "cwd": str(project),
                                                       "initial_judgment_scope": initial_scope})
            with (round_dir / "stderr.log").open("w", encoding="utf-8") as stderr, \
                    (round_dir / "events.jsonl").open("w", encoding="utf-8") as events:
                with self.lock:
                    if run_id in self.cancelled or self.closed:
                        raise ValueError("Run was cancelled before launch.")
                    process = subprocess.Popen(command, cwd=project, stdin=subprocess.PIPE,
                                               stdout=subprocess.PIPE, stderr=stderr, text=True,
                                               encoding="utf-8", errors="replace", start_new_session=True)
                    self.processes[run_id] = process
                    run.update(status="running", pid=process.pid)
                    write_json(path, run)
                process.stdin.write(text)
                process.stdin.close()
                for line in process.stdout:
                    events.write(line)
                    events.flush()
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    if event.get("type") == "thread.started" and nonempty(event.get("thread_id")):
                        session = event["thread_id"]
                        if run["session_id"] and session != run["session_id"]:
                            raise ValueError("Codex returned a different session ID during resume.")
                        run["session_id"] = session
                        with self.lock:
                            write_json(path, run)
                    if event.get("type") == "turn.failed":
                        run["turn_failed"] = event.get("error") or "Codex reported turn.failed."
                    # Only transport events can confirm runtime settings; worker prose cannot.
                    if event.get("type") in ("thread.started", "session_config", "session.configured"):
                        for source, target in (("model", "observed_model"), ("reasoning_effort", "observed_effort")):
                            if nonempty(event.get(source)):
                                run[target] = event[source]
                run["exit_code"] = process.wait()
            report = read_json(result_path) if result_path.exists() else None
            if not valid_report(report):
                raise ValueError(f"Codex exited with code {run['exit_code']} without a valid structured report. "
                                 f"Read {round_dir / 'stderr.log'} for the actual CLI error.")
            run["report"] = report
            run["report_path"] = str(result_path)
            if run_id in self.cancelled:
                run["status"] = "cancelled"
            elif run["exit_code"] != 0 or not run["session_id"] or run["turn_failed"]:
                run["status"] = "failed"
                run["error"] = (str(run["turn_failed"]) if run["turn_failed"] else
                                "Codex exited unsuccessfully or did not provide an actual session ID.")
            else:
                run["status"] = report["status"]
            if (run["status"] == "completed" and not run["initial_complete"]
                    and initial_scope and report["evidence"] and not report["files_changed"]):
                with self.lock:
                    self._initial_record(run, result_path)
                    run["initial_complete"] = True
                    run["initial_report"] = str(result_path)
            elif run["status"] == "completed" and not run["initial_complete"]:
                run["error"] = "Initial judgment needs evidence and no reported project edits; participation is incomplete."
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            if process is not None and process.poll() is None:
                self._stop(process)
            run["status"] = "cancelled" if run_id in self.cancelled or self.closed else "failed"
            run["error"] = str(error)
        finally:
            if acquired:
                self.slots.release()
            with self.lock:
                self.processes.pop(run_id, None)
                self.active.discard(run_id)
                if process is not None:
                    run["exit_code"] = process.poll()
                run.update(updated_at=now(), pid=None)
                write_json(path, run)
        return self._compact(run)

    def _initial_record(self, run: dict, report_path: Path) -> None:
        evidence = [str(report_path.relative_to(Path(run["project"])))]
        ledger.record(Path(run["project"]), {
            "id": f"forge-initial-{run['persona']}-{run['run_id'][:8]}", "task": run["task_id"],
            "persona": run["persona"], "mode": "delegated_subagent", "actor": run["session_id"],
            "trigger": "Maverick Forge first independent returned judgment", "kind": "direction",
            "contribution": run["report"]["summary"], "status": "reviewed", "outcome": run["report"]["next_step"] or run["report"]["summary"],
            "evidence": evidence, "impact": None, "phase": "initial", "reused": run["round"] > 1,
        })

    @staticmethod
    def _compact(run: dict) -> dict:
        keys = ("run_id", "task_id", "persona", "session_id", "round", "status", "operation",
                "initial_complete", "requested_model", "requested_effort", "observed_model",
                "observed_effort", "report", "report_path", "round_dir", "error", "exit_code")
        return {key: run.get(key) for key in keys}

    def status(self, project: str, task_id: str) -> dict:
        project_path = self._project(project)
        task = self._task(project_path, task_id)
        with self.lock:
            runs = {role: self._refresh(task / role / "run.json") for role in PERSONAS
                    if (task / role / "run.json").exists()}
            sessions = [run["session_id"] for run in runs.values() if run.get("initial_complete")]
            conflict = len(sessions) != len(set(sessions))
            complete = [role for role in PERSONAS if runs.get(role, {}).get("initial_complete")]
            if conflict:
                complete = []
            decision = read_json(task / "decision.json") if (task / "decision.json").exists() else None
            return {"task_id": task_id, "initial_complete": not conflict and len(complete) == 5 and bool(decision),
                    "completed_personas": (["maverick"] if decision else []) + complete,
                    "missing_personas": ([] if decision else ["maverick"]) + [r for r in PERSONAS if r not in complete],
                    "session_identity_conflict": conflict, "decision": decision,
                    "workers": {role: self._compact(run) for role, run in runs.items()}}

    def decide(self, project: str, task_id: str, decision: str) -> dict:
        if not nonempty(decision):
            raise ValueError("decision must explain the selected route and meaningful alternatives.")
        project_path = self._project(project)
        task = self._task(project_path, task_id)
        with self.lock:
            state = self.status(str(project_path), task_id)
            missing = [r for r in state["missing_personas"] if r != "maverick"]
            if missing or state["session_identity_conflict"]:
                raise ValueError(f"Five real independent judgments are not complete: {', '.join(missing)}")
            path = task / "decision.json"
            value = {"task_id": task_id, "controller": "maverick", "runtime": "AGY",
                     "decision": decision, "at": now()}
            write_json(path, value)
            ledger.record(project_path, {
                "id": "forge-initial-maverick", "task": task_id, "persona": "maverick",
                "mode": "direct", "actor": "maverick", "trigger": "Five independent Codex judgments returned",
                "kind": "direction", "contribution": decision, "status": "reviewed", "outcome": decision,
                "evidence": [str(path.relative_to(project_path))], "impact": None, "phase": "initial",
            })
        return {"status": "decided", "task_id": task_id, "decision": decision, "initial_complete": True}

    def record(self, project: str, task_id: str, persona: str, kind: str, contribution: str,
               outcome: str, evidence: list[str], impact: int | None,
               status: str = "confirmed", event_id: str | None = None, shift: dict | None = None) -> dict:
        project_path = self._project(project)
        task = self._task(project_path, task_id)
        if persona not in ("maverick", *PERSONAS):
            raise ValueError("Unknown persona.")
        with self.lock:
            if persona == "maverick":
                if not (task / "decision.json").exists():
                    raise ValueError("Record the Maverick synthesis with forge_decide first.")
                actor, mode = "maverick", "direct"
            else:
                path = task / persona / "run.json"
                run = read_json(path) if path.exists() else {}
                if not run.get("initial_complete") or not run.get("session_id"):
                    raise ValueError("This persona has no completed independent Codex judgment.")
                actor, mode = run["session_id"], "delegated_subagent"
            event = {"id": event_id or f"forge-{persona}-{uuid.uuid4().hex[:12]}", "task": task_id,
                     "persona": persona, "mode": mode, "actor": actor,
                     "trigger": "Maverick assessed the returned work against actual outcomes",
                     "kind": kind, "contribution": contribution, "status": status, "outcome": outcome,
                     "evidence": evidence, "impact": impact}
            if event_id:
                previous = next((item for item in ledger._task_events(project_path, task_id)
                                 if item['id'] == event_id), None)
                if previous:
                    # Assessing a returned initial opinion must not change its recorded phase.
                    for key in ("phase", "reused"):
                        if key in previous:
                            event[key] = previous[key]
            if shift is not None:
                event["shift"] = shift
            return ledger.record(project_path, event)

    def report(self, project: str, task_id: str) -> dict:
        project_path = self._project(project)
        state = self.status(str(project_path), task_id)
        with self.lock:
            ledger_path = project_path / ".maverick/contributions.jsonl"
            body = ledger.report(project_path, task_id) if ledger_path.exists() else "尚无贡献记录。\n"
        heading = (f"# Maverick Forge · {task_id}\n\n"
                   f"桥接实际返回与主控综合：{len(state['completed_personas'])}/6。"
                   f"缺少：{', '.join(state['missing_personas']) or '无'}。\n\n"
                   "参与依据是本桥保存的 Codex 会话 ID、退出结果与结构化报告；"
                   "贡献影响仍由 Maverick 根据实际证据判断，不自动打分。\n\n")
        return {"task_id": task_id, "initial_complete": state["initial_complete"],
                "missing_personas": state["missing_personas"],
                "workers": {role: {key: value for key, value in worker.items() if key != "report"}
                            for role, worker in state["workers"].items()},
                "markdown": heading + body}

    @staticmethod
    def _stop(process: subprocess.Popen) -> None:
        if process.poll() is not None:
            return
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except ProcessLookupError:
            return
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            process.wait()

    def cancel(self, run_id: str) -> dict:
        with self.lock:
            _, run = self._run(run_id)
            process = self.processes.get(run_id)
            if process is None and run["status"] not in ("queued", "starting", "running"):
                return {"run_id": run_id, "status": run["status"], "cancelled": False}
            if process is None and run["status"] == "running":
                raise ValueError("This server no longer owns that process; inspect it before restarting. No unrelated process was signalled.")
            self.cancelled.add(run_id)
        if process is not None:
            self._stop(process)
        return {"run_id": run_id, "status": "cancellation_requested", "cancelled": True}

    def close(self) -> None:
        with self.lock:
            self.closed = True
            processes = list(self.processes.items())
            self.cancelled.update(self.processes)
        for _, process in processes:
            self._stop(process)

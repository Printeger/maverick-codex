#!/usr/bin/env python3
"""Stdlib stdio MCP server. Long calls return after Codex; AGY handles background wakeup."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from forge import VERSION
from forge.runtime import ForgeRuntime, PERSONAS


def string(description: str = "") -> dict:
    return {"type": "string", "description": description}


PROJECT = string("Absolute initialized project directory; matches this MCP server's project.")
TASK = string("Stable user-level task ID. Continue using it for follow-ups and milestones.")
RUN = string("Actual run_id returned by forge_dispatch or forge_status; identity cannot change.")


def tool(name: str, description: str, properties: dict, required: tuple[str, ...]) -> dict:
    return {"name": name, "description": description,
            "inputSchema": {"type": "object", "properties": properties,
                            "required": list(required), "additionalProperties": False}}


TOOLS = [
    tool("forge_dispatch", "Start one real independent Codex persona judgment. Call once for each of the five personas. "
         "AGY runs this tool in the background and receives its final result automatically; do not poll. "
         "Full OS access, fixed role model, at most two running Codex processes.",
         {"project": PROJECT, "task_id": TASK, "persona": {"type": "string", "enum": list(PERSONAS)},
          "prompt": string("Goal, actual boundaries and primary evidence; do not predetermine the answer.")},
         ("project", "task_id", "persona", "prompt")),
    tool("forge_resume", "Continue the same persona's exact saved Codex session with new evidence or a concrete next action. "
         "Before forge_decide, follow-up remains initial judgment work. A launch that never produced a session can be retried here. "
         "Background return, no polling.",
         {"run_id": RUN, "prompt": string("New evidence, chosen route and current assignment; no full-history replay.")},
         ("run_id", "prompt")),
    tool("forge_status", "Read saved results once when recovering context or when the user asks for progress. Not a polling loop.",
         {"project": PROJECT, "task_id": TASK}, ("project", "task_id")),
    tool("forge_cancel", "Cancel a queued or running call owned by this bridge. Does not signal unrelated processes.",
         {"run_id": RUN}, ("run_id",)),
    tool("forge_decide", "Maverick records the synthesis after all five distinct Codex judgments really returned. "
         "Explain chosen mechanism, how the judgments changed the route, alternatives set aside and next action. No consensus vote.",
         {"project": PROJECT, "task_id": TASK, "decision": string("The actual AGY Maverick synthesis.")},
         ("project", "task_id", "decision")),
    tool("forge_record", "Record actual contribution impact after assessing outcomes. Attendance alone has no grade. "
         "This cannot fabricate participation for a persona without a returned session.",
         {"project": PROJECT, "task_id": TASK,
          "persona": {"type": "string", "enum": ["maverick", *PERSONAS]},
          "kind": {"type": "string", "enum": ["direction", "implementation", "correction"]},
          "contribution": string("What this persona actually contributed."),
          "outcome": string("Observed effect or the fact that impact is still unknown."),
          "evidence": {"type": "array", "items": string("Actual result, file or decision reference.")},
          "impact": {"type": ["integer", "null"], "enum": [1, 2, 3, None]},
          "status": {"type": "string", "enum": ["reviewed", "proposed", "confirmed", "not_adopted", "unknown"],
                     "default": "confirmed"},
          "event_id": string("Optional existing event ID to revise an impact assessment without changing its identity."),
          "shift": {"type": "object", "properties": {"before": string(), "after": string()},
                    "required": ["before", "after"], "additionalProperties": False}},
         ("project", "task_id", "persona", "kind", "contribution", "outcome", "evidence", "impact")),
    tool("forge_report", "Generate the six-person contribution report at task or milestone completion. "
         "Reports actual session coverage separately from evidence-based impact; never grants automatic credit.",
         {"project": PROJECT, "task_id": TASK}, ("project", "task_id")),
]
TOOL_MAP = {item["name"]: item for item in TOOLS}


class Server:
    def __init__(self, runtime: ForgeRuntime):
        self.runtime = runtime
        self.output_lock = threading.Lock()
        self.calls_lock = threading.Lock()
        self.calls: dict = {}
        self.threads: list[threading.Thread] = []

    def send(self, payload: dict) -> None:
        with self.output_lock:
            sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
            sys.stdout.flush()

    def call(self, request: dict) -> None:
        def on_start(run_id: str) -> None:
            with self.calls_lock:
                context = self.calls[request["id"]]
                context["run_id"] = run_id
                cancelled = context["cancelled"]
            if cancelled:
                self.runtime.cancel(run_id)

        try:
            params = request.get("params", {})
            name, arguments = params.get("name"), params.get("arguments", {})
            if name not in TOOL_MAP or not isinstance(arguments, dict):
                raise ValueError("Unknown tool or invalid arguments.")
            schema = TOOL_MAP[name]["inputSchema"]
            missing = set(schema["required"]) - arguments.keys()
            unknown = arguments.keys() - schema["properties"].keys()
            if missing or unknown:
                raise ValueError(f"Tool arguments: missing={sorted(missing)}, unknown={sorted(unknown)}")
            extra = {"_on_start": on_start} if name in ("forge_dispatch", "forge_resume") else {}
            result = getattr(self.runtime, name.removeprefix("forge_"))(**arguments, **extra)
            value = {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                     "isError": False}
        except Exception as error:
            value = {"content": [{"type": "text", "text": str(error)}], "isError": True}
        finally:
            with self.calls_lock:
                self.calls.pop(request["id"], None)
        self.send({"jsonrpc": "2.0", "id": request["id"], "result": value})

    def cancel_request(self, request_id) -> None:
        with self.calls_lock:
            context = self.calls.get(request_id)
            if context is None:
                return
            context["cancelled"] = True
            run_id = context["run_id"]
        if run_id:
            try:
                self.runtime.cancel(run_id)
            except ValueError:
                pass  # The owned call may have finished concurrently.

    def run(self) -> None:
        try:
            for line in sys.stdin:
                if not line.strip():
                    continue
                try:
                    request = json.loads(line)
                    if not isinstance(request, dict):
                        raise ValueError("JSON-RPC request must be an object.")
                except ValueError as error:
                    self.send({"jsonrpc": "2.0", "id": None,
                               "error": {"code": -32700, "message": str(error)}})
                    continue
                if "id" not in request:
                    if request.get("method") == "notifications/cancelled":
                        self.cancel_request(request.get("params", {}).get("requestId"))
                    continue
                method = request.get("method")
                if method == "tools/call":
                    with self.calls_lock:
                        self.calls[request["id"]] = {"run_id": None, "cancelled": False}
                    thread = threading.Thread(target=self.call, args=(request,))
                    self.threads = [active for active in self.threads if active.is_alive()]
                    self.threads.append(thread)
                    thread.start()
                    continue
                if method == "initialize":
                    requested = request.get("params", {}).get("protocolVersion")
                    version = requested if requested in ("2024-11-05", "2025-03-26", "2025-06-18") else "2024-11-05"
                    result = {"protocolVersion": version, "capabilities": {"tools": {"listChanged": False}},
                              "serverInfo": {"name": "maverick-forge", "version": VERSION}}
                elif method == "tools/list":
                    result = {"tools": TOOLS}
                elif method == "ping":
                    result = {}
                else:
                    self.send({"jsonrpc": "2.0", "id": request["id"],
                               "error": {"code": -32601, "message": "Method not found"}})
                    continue
                self.send({"jsonrpc": "2.0", "id": request["id"], "result": result})
        finally:
            self.runtime.close()
            for thread in self.threads:
                thread.join(timeout=5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", help="Absolute project path; defaults to MAVERICK_PROJECT.")
    args = parser.parse_args()
    Server(ForgeRuntime(project=args.project)).run()


if __name__ == "__main__":
    main()

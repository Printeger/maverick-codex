# Working on Maverick Codex itself

This repository contains an installer and source material, not an initialized user project.
Keep V1 small: six reusable personalities, on-demand knowledge, project-local installation,
manual updates and a short initialization check. No evaluation service, auto-evolution loop,
database, daemon, or automatic commits in installed projects.

Source personalities live in `personas/`; knowledge lives in `knowledge/`; neither should
contain private details from a user's project. The installer assembles a self-contained
project skill from `skills/maverick/`, the source documents and its own script.

Preserve target AGENTS.md/configuration and report static and live verification separately.
Verify installer changes with `python3 tests/smoke.py`; do not build a personality benchmark.

# Working on Maverick Codex itself

This repository contains an installer and source material, not an initialized user project.
Keep V1.1 small: six reusable personalities, problem-driven thinking, on-demand knowledge,
project-local installation, a factual contribution ledger and manual personality updates.
No evaluation service, auto-evolution loop,
database, daemon, or automatic commits in installed projects.

Source personalities live in `personas/`; knowledge lives in `knowledge/`; neither should
contain private details from a user's project. The installer assembles a self-contained
project skill from `skills/maverick/`, the source documents and its own script.

Preserve target AGENTS.md/configuration and report static and live verification separately.
Preserve existing project knowledge, state and preferences during upgrades. Distinguish
Maverick using a perspective from an actual subagent. Credit only evidenced outcomes.
Verify changes with `python3 tests/smoke.py`, which includes the contribution checks;
do not build a personality benchmark.

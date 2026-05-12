# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What Minerva Is

Minerva is a **CPU-local reliability kernel** that turns CI/CD, agent, and ops failures into structured observations, policy-gated decisions, and eval feedback. It is read-only by default and has no required remote LLM dependency — a deterministic baseline interpreter handles the minimum path.

Core invariant (do not break):

```text
LLM interprets. Policy authorizes. Executor acts.
```

The project ships as a single Python package `minerva_kernel`, a `minerva` CLI, and a GitHub Action (`action.yml`).

## Common Commands

```bash
# Install in-place (no deps; this package has zero runtime dependencies)
python3 -m pip install --no-deps .

# Full test suite (uses stdlib unittest; pytest config is in pyproject.toml)
python3 -m unittest discover -s tests
python3 -m pytest tests/ -v        # equivalent

# Run a single test module / case
python3 -m unittest tests.test_policy
python3 -m unittest tests.test_policy.PolicyTest.test_specific_case

# Eval smoke (gates CI; must pass 5/5)
python3 -m minerva_kernel.eval_smoke

# Lint (project uses ruff in the user's global workflow; no repo config)
ruff check minerva_kernel tests

# The exact CI smoke command Minerva runs on itself in GitHub Actions:
minerva observe -- bash -c 'python3 -m compileall minerva_kernel && python3 -m unittest discover -s tests && python3 -m minerva_kernel.eval_smoke'
```

CLI surface (all subcommands of `minerva`):

```bash
minerva diagnose observation.json          # propose a Decision from an Observation
minerva observe -- <command>               # run a command, capture Observation, save run record
minerva ci-analyze <log>                   # diagnose a CI log tail
minerva execute-action decision.json --observation obs.json --cwd .
                                           # explicit, policy-checked read-only follow-up
minerva policy-check decision.json         # validate a Decision against policy
minerva render-ci-summary <run.json>       # Markdown for $GITHUB_STEP_SUMMARY
minerva render-ci-artifact <run.json>      # JSON artifact (minerva_ci_run.v0)
minerva minervad --host 127.0.0.1 --port 8765   # local-only prototype health server
minerva provider-health --base-url ... --model ...  # probe optional local OpenAI-compatible provider
minerva doctor                             # local setup check
```

Run records are written to `.minerva/runs/*.json`. The CI workflow picks the newest record and renders it.

## Architecture (Big Picture)

Data flows through stable, versioned schemas. The two anchor types live in `minerva_kernel/types.py`:

- `Observation` (v0): command, cwd, exit_code, stdout/stderr tails, duration, source, policy_summary, redactions.
- `Decision` (v0): one action from `INSTRUCTION_SET_V0`, plus rationale, risk, evidence. Actions are a closed set — extending it is a schema change.

Pipeline (`sdk.diagnose_observation`):

```text
Observation
  → redact (redaction.py — strips secrets BEFORE any model sees it)
  → propose Decision
       ├── no provider → baseline.propose_baseline_decision (deterministic, CPU-only)
       └── provider    → planner.build_prompt → router.LocalLLMRouter → provider.complete
  → validate_action (policy.py — checks instruction is in set, action class is read-only,
                     rejects shell/write tools and destructive command patterns)
  → Diagnosis(decision, policy_decision, redactions)
```

Key module map:

| File | Role |
|---|---|
| `types.py` | `Observation`, `Decision`, `INSTRUCTION_SET_V0`, `PolicyDecision`. Frozen dataclasses. |
| `redaction.py` | Pattern-based secret redaction. Always runs before prompt construction. |
| `baseline.py` | Deterministic CPU-local interpreter for common failure signatures. The "no provider" path. |
| `providers.py` | `ModelProvider` protocol, `LocalOpenAICompatibleProvider`, `MockModelProvider`, health probe. There is **no** remote LLM fallback. |
| `planner.py` / `router.py` | Build structured prompts; route to a local provider. |
| `policy.py` | Allow-list of read-only actions (`READ_ONLY_ACTIONS`), deny-list of write/shell tools and destructive command patterns. The only authorizer. |
| `executor.py` | Bounded read-only diagnostic actions for `execute-action`. Never auto-invoked by `observe`. |
| `observe.py` | Runs a subprocess, captures Observation, writes run record. |
| `ci_analyze.py` / `ci_render.py` | CI log → Observation; run record → Markdown / JSON artifact. |
| `sdk.py` | `Minerva` facade, `Diagnosis`, `diagnose_observation` — the supported Python entry point. |
| `daemon.py` | `minervad` prototype health server (local-only). |
| `cli.py` | Argparse dispatcher for all `minerva ...` subcommands. |

### Hard constraints enforced by tests

These are the project's non-negotiables. Tests fail loudly if you violate them:

- **CPU-only, sub-500M model target.** No CUDA, no remote API required for the minimum path.
- **No automatic remote LLM fallback.** If a provider isn't configured, the baseline runs — silently. Don't add an "if baseline weak, call cloud" branch.
- **Read-only by default.** `execute_action` only runs actions in `READ_ONLY_ACTIONS` and rejects shell/write tools. `observe` never calls `execute-action` itself.
- **Redaction happens before the model sees text**, not after. See `Observation.redacted()`.
- **Decisions are structured.** Action must be in `INSTRUCTION_SET_V0`. Free-text rationale is explanation only, never an execution channel.
- **Zero runtime dependencies.** `pyproject.toml` deliberately has `dependencies = []`. Don't add a runtime dep without explicit approval.

## CI and Public Site

Two GitHub Actions workflows live in `.github/workflows/`:

- `ci.yml` — runs Minerva on itself: `minerva observe -- <compile + unittest + eval_smoke>`. Exits with the **observed** command's status, not Minerva's. Always uploads `minerva-ci-run.json` if a run record exists.
- `pages.yml` — validates and (on `workflow_dispatch`) deploys `public-site/` to GitHub Pages at `minervakernel.com`. The custom-domain artifact is `public-site/CNAME`. Pages deploys ONLY via GitHub Actions — do not deploy `public-site/` from a private server.

Before claiming public-domain readiness, run:

```bash
python3 scripts/check-release-readiness.py --content-reviewed "..."
# Or fully offline:
python3 scripts/check-release-readiness.py --skip-external --install-backend auto
```

This checker enforces TLS, requires Minerva brand signals, and **rejects VoxSign markers** in any public artifact. Brand contamination is a release blocker.

## Local AI Team Loop

`.tasks/` is a local task queue (T1..Tn cards + `board.md`). `scripts/ai-team-tick.sh` runs one bounded task chain — installable as a launchd or systemd-user timer. Two safety scripts gate every tick and must keep passing:

- `scripts/check-project-boundary.sh` — confirms cwd is the Minerva root (rejects `/Users/zouyongming/VoxSign*` paths).
- `scripts/check-contamination.sh` — confirms no VoxSign content leaked in.

Do not modify the boundary/contamination scripts to "pass" — they exist precisely because a sibling Claude session previously contaminated this repo with VoxSign-scoped changes. If they fail, stop and investigate.

The executor is selected by `MINERVA_AI_EXECUTOR` (`auto` | `codex` | `claude`). Project root override: `MINERVA_PROJECT_ROOT`. Per-tick cap: `MINERVA_AI_MAX_TASKS_PER_TICK` (default 4).

## Working Rules Specific to This Repo

- **Test runner is `unittest`.** CI runs `python3 -m unittest discover -s tests`. Tests must run under stdlib unittest (pytest is fine locally but no pytest-only features in test files).
- **One package, flat-ish structure.** Don't introduce subpackages under `minerva_kernel/` unless splitting a single module exceeds ~400 lines or there's a clear seam (e.g. `providers/`).
- **Schemas are versioned (`v0`).** Adding a field is fine if optional and backward-compatible. Renaming or removing fields requires a `v1` and an explicit migration note.
- **Don't auto-execute proposed actions.** `observe` ends with the run record. `execute-action` is a separate, explicit command. Never wire them together.
- **Public-site changes go through `pages.yml`**, not any deploy script. `49.51.134.101` and `43.165.70.88` are VoxSign infrastructure — Minerva does not touch them.
- **GitHub issues are the durable source of truth for tasks.** `.tasks/T*.md` cards are local execution handles; their numeric IDs map to GitHub issue numbers in `board.md`.

## Repository Roadmap Anchor

Milestones in `ROADMAP.md`: **M0** (local failure interpreter — current) → M1 (CI triage) → M2 (local model bench) → M3 (agent tool-call guard SDK) → M4 (`minervad` daemon). The repo is currently at M0 release-readiness; new features should target M1+ unless they close an M0 blocker.

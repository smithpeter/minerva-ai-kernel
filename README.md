# Minerva

Minerva is a CPU-local reliability kernel for agents, CI/CD, and AIOps.

It turns failures into structured observations, policy-gated decisions, and
eval feedback loops without requiring a remote model for the minimum path.

Project domain:

```text
minervakernel.com
```

Standalone public page artifact:

- [public-site/index.html](public-site/index.html)
- [public-site/CNAME](public-site/CNAME)
- [GitHub Pages public-site deployment workflow](.github/workflows/pages.yml)
- [minervakernel.com domain cutover runbook](docs/minervakernel-domain-cutover-runbook.md)

## 30-Second Example

```bash
python3 -m pip install --no-deps .
minerva ci-analyze examples/logs/missing-dependency.log --job-name demo
```

Expected shape:

```text
Failure: missing_dependency
Action: inspect_dependencies
Policy decision: allowed
Policy decision reason: allowed by read-only policy
```

Minerva reports the next safe diagnostic step. It does not install packages,
edit files, retry jobs, or auto-repair systems.

## Five-Minute Demo

Start with the [five-minute demo](docs/five-minute-demo.md):

```bash
minerva ci-analyze examples/logs/missing-dependency.log --job-name demo
python3 -m minerva_kernel.eval_smoke
```

For GitHub Actions, see [GitHub Action usage](docs/github-action.md).

## Core Interfaces

```bash
minerva ci-analyze build.log
minerva observe -- pytest
minerva diagnose observation.json
minerva minervad --host 127.0.0.1 --port 8765
```

With no configured provider, Minerva uses a deterministic CPU-local baseline
interpreter for common failure signatures. Explicit local providers remain
optional, and there is no automatic remote LLM fallback.

Explicit read-only follow-up is available through:

```bash
minerva execute-action decision.json --observation observation.json --cwd .
```

This path is never called automatically by `observe`; it policy-checks the
decision again and only gathers bounded diagnostic evidence.

## Non-Negotiable Constraints

- CPU-only minimum runtime
- sub-500M model target
- no remote LLM required for minimum function
- structured output
- policy-gated execution
- read-only by default

## M2 Real Numbers — Baseline vs First Sub-500M Candidate

Against the 30-case CPU model eval corpus (`evals/cpu_model_cases.jsonl`),
measured 2026-05-13:

| Metric | Baseline (deterministic) | Qwen2.5-Coder-0.5B (Ollama, CPU) |
|---|---|---|
| JSON validity | 100% | 100% |
| Dangerous action rate | 0% | 0% |
| Failure-label accuracy | **20%** | **0%** |
| Safe-recovery decision rate | **29.4%** | **0%** |
| Escalation recall | 0% | 100% (provider fallback, not model) |
| p95 latency | **3 ms** | **20 022 ms** |
| Overall | floor | **retest** (does not clear the floor) |

**The first sub-500M candidate is currently worse than the baseline.**
The reason is diagnostic: under the default prompt, Qwen2.5-Coder-0.5B
returns only `{"action": "..."}` and gets rejected by Minerva's
strict `decision.v0` parser, falling through to the provider's
hard-coded escalation fallback. Full analysis, per-category
breakdown, and what M2 should try next:
[docs/m2-baseline-floor.md](docs/m2-baseline-floor.md).

Reproduce:

```bash
# Baseline only (no model weights, no network)
python3 -m minerva_kernel.cpu_model_eval --provider baseline

# Real candidate (needs `ollama pull qwen2.5-coder:0.5b` first)
python3 -m minerva_kernel.cpu_model_eval \
  --provider local-openai --model qwen2.5-coder:0.5b \
  --base-url http://127.0.0.1:11434/v1/chat/completions --timeout 60
```

## Core Principle

```text
LLM interprets. Policy authorizes. Executor acts.
```

## Project Docs

Start here:

- [Minimal Python SDK decision example](examples/minimal_sdk_decision.py)
- [sample-consumer — drop-in template for using Minerva from another repo](examples/sample-consumer/README.md)
- [Five-minute demo](docs/five-minute-demo.md)
- [GitHub Action usage](docs/github-action.md)
- [Agent tool failure guide](examples/agent-tool-failure.md)
- [Explicit execute-action demo](examples/execute-action-demo.md)
- [Integration recipes for CI, SDK, and agents](docs/integration-recipes.md)
- [Adapter event reporting guide](docs/adapter-event-reporting.md)
- [Agent-era value analysis](docs/agent-era-value-analysis.md)
- [Minervad prototype health and diagnosis endpoint](docs/minervad-prototype.md)
- [M1 roadmap task seeds](docs/m1-roadmap-task-seeds.md)
- [M0 release readiness checklist](docs/m0-release-readiness.md)
- [M0 local release dry-run guide](docs/m0-local-release-dry-run.md)
- [Standalone Minerva public page artifact](public-site/index.html)
- [GitHub Pages public-site deployment workflow](.github/workflows/pages.yml)
- [minervakernel.com domain cutover runbook](docs/minervakernel-domain-cutover-runbook.md)
- [M0 launch blog post draft](docs/m0-launch-blog-post.md)
- [M0 demo script](examples/m0-demo-script.md)
- [Model strategy and local provider path](docs/model-strategy.md)
- [Sub-500M CPU model plan and eval report shape](docs/sub-500m-cpu-model-plan.md)
- [M2 baseline floor — real numbers from `--provider baseline`](docs/m2-baseline-floor.md)
- [CPU-local model candidate registry](models/cpu_model_candidates.json)
- [CPU model eval scoring contract](docs/cpu-model-eval-scoring-contract.md)
- [Local CPU model runbook](docs/local-cpu-model-runbook.md)
- [Product strategy](docs/product-strategy.md)
- [Questions and requirements](docs/questions-and-requirements.md)
- [Execution plan and founder role](docs/execution-plan-and-founder-role.md)
- [AI team execution system](docs/ai-team-execution-system.md)
- [Plan-Eng-Review workflow for AI-team tasks](docs/plan-eng-review-workflow.md)
- [AI team task template](docs/ai-team-task-template.md)
- [AI team timer runbook](docs/ai-team-timer-runbook.md)
- [Complete vision execution queue](docs/complete-vision-execution-queue.md)
- [Open-source launch checklist](docs/open-source-launch-checklist.md)
- [Path to 95% launch credibility](docs/path-to-95.md)
- [Most important next step](docs/most-important-next-step.md)
- [GitHub issues](docs/github-issues.md)
- [Shared tools, isolated state](docs/shared-tools-isolated-state.md)
- [Failure case contribution guide](docs/failure-case-contributions.md)
- [Ecosystem contribution guide](docs/ecosystem-contributions.md)

Project contact: `maintainers@minervakernel.com`. Security reports:
`security@minervakernel.com`.

## Repository Status

This repository is being initialized from the Minerva research workspace. The first implementation target is `minerva observe -- <command>`.

## CI Gate

Every push and pull request runs the GitHub Actions CI smoke gate through
Minerva on Python 3.11:

```bash
minerva observe -- bash -c 'python3 -m compileall minerva_kernel && python3 -m unittest discover -s tests && python3 -m minerva_kernel.eval_smoke'
```

The workflow writes `minerva render-ci-summary` output to
`$GITHUB_STEP_SUMMARY` and saves a redacted `minerva-ci-run.json` artifact from
`minerva render-ci-artifact` when a run record exists. The integration is
diagnostic only: it publishes bounded evidence, exits with the observed command
status, and does not perform auto-repair or execute Minerva-proposed actions.

Before a public release, collect repeatable GitHub Actions and
`minervakernel.com` DNS/TLS/HTTPS and brand-contamination evidence with:

```bash
python3 scripts/check-release-readiness.py --content-reviewed "Verified public Minerva page"
```

The readiness checker keeps TLS verification enabled, requires Minerva
brand/content signals in the public HTTPS page, and rejects VoxSign markers in
redirects or page content. The `--content-reviewed` note records human review;
it does not override TLS validation or the automated brand guard.
Serve [public-site/index.html](public-site/index.html) for the intended static
Minerva page, and use the
[domain cutover runbook](docs/minervakernel-domain-cutover-runbook.md) for
nginx/static-host, certificate, rollback, and verification steps.

The repository includes a GitHub Pages deployment workflow at
[.github/workflows/pages.yml](.github/workflows/pages.yml). On `main` changes
to the public-site artifact, or on manual dispatch, it validates the static
artifact, uploads `public-site/` with `actions/upload-pages-artifact`, and
deploys it with `actions/deploy-pages`. The custom-domain artifact is
[public-site/CNAME](public-site/CNAME), containing `minervakernel.com`.
Workflow success only proves the Pages artifact was published; the release
owner must still configure/verify the GitHub Pages custom domain, DNS records,
managed certificate, HTTPS content, and brand-contamination checks before
claiming public domain readiness. The Pages path does not use private server
credentials or deploy to `49.51.134.101`.

For local offline editable-install readiness without network access, run:

```bash
python3 scripts/check-release-readiness.py --skip-external --install-backend auto
```

The `local_install_backend` check reports whether `setuptools.build_meta` is
importable in a bounded set of local Python candidates and reports the selected
passing candidate. `pass` means the documented `--no-build-isolation -e .`
install has a local build backend available. `fail` reports a bounded list of
failed candidates; use a local interpreter or venv that already includes the
backend, or seed it from an approved local wheel/cache before rerunning. The
readiness checker does not download dependencies.

Use `--install-backend current --install-backend-python PYTHON` to verify one
exact target interpreter, or `--install-backend fresh-venv` to verify whether a
fresh virtualenv created from the selected interpreter is seeded with the
backend.

For the local release owner's daily dashboard, run:

```bash
python3 scripts/release-ops-dashboard.py
```

The dashboard stays local-only by default. It summarizes Plan-Eng-Review
health, AI-team queue state, eval smoke, CPU eval fixture status, local install
readiness, task queue completion, and worktree cleanliness as
`release_ops_status.v0`. Use `--json` for machine-readable output or
`--no-fail` when you want a report even if blockers remain.

When the dashboard reports a dirty worktree, generate the bounded handoff
inventory with:

```bash
python3 scripts/release-handoff.py
```

The handoff emits `minerva.release_handoff.v0` with dashboard status,
changed-file category counts, blockers, and next actions. It reports paths and
categories only; it does not dump file contents or call external services.

## Local AI Team

Minerva has a local task board in `.tasks/` and a scoped agent loop:

```bash
bash scripts/minerva-ai-team-status.sh
bash scripts/ai-team-preflight.sh
bash scripts/check-project-boundary.sh
bash scripts/check-contamination.sh
bash scripts/agent-loop.sh T1
```

By default these scripts are scoped to `/Users/zouyongming/projects/minerva-ai-kernel`.
On another machine, set `MINERVA_PROJECT_ROOT` to that clone path before running the automation.
They must not be used from VoxSign.

For bounded automation, run one task tick:

```bash
bash scripts/ai-team-tick.sh
```

The tick includes an autopilot finalizer. When a worker marks a task card
`done`, the finalizer runs boundary checks, contamination checks, compile/tests,
commits, pushes, and tries to update the linked GitHub issue. A single tick can
chain multiple pending tasks until the queue is empty or
`MINERVA_AI_MAX_TASKS_PER_TICK` is reached.

To install a macOS `launchd` job that runs one tick every 30 minutes:

```bash
bash scripts/install-ai-team-launchd.sh
```

To install a Linux `systemd --user` timer that runs one tick every 30 minutes:

```bash
bash scripts/install-ai-team-systemd-user.sh
```

To stop macOS automation:

```bash
bash scripts/uninstall-ai-team-launchd.sh
```

To stop Linux automation:

```bash
bash scripts/uninstall-ai-team-systemd-user.sh
```

Check Linux timer status and logs:

```bash
systemctl --user status minerva-ai-team-tick.timer
journalctl --user -u minerva-ai-team-tick.service -n 100
```

The local loop supports Codex and Claude Code:

```bash
MINERVA_AI_EXECUTOR=codex bash scripts/ai-team-tick.sh
MINERVA_AI_EXECUTOR=claude bash scripts/ai-team-tick.sh
```

Default mode is `auto`, which prefers Codex when available.

# Changelog

## M0 / M1-Prep Public Update Draft - 2026-05-08

Minerva has reached an M0-ready local release shape and has seeded the M1
product loop. The current project claim remains narrow:

```text
Minerva is a CPU-local failure interpreter for CI/CD, agents, and ops.
```

M0 proves the first local loop: observe a command failure, structure the
failure state, produce a bounded decision, run the decision through policy, and
save local evidence for review and evaluation.

### Current Capabilities

- `minerva doctor` verifies that the local repository skeleton is usable.
- `minerva observe -- <command>` runs a command, captures bounded stdout and
  stderr tails, exit code, duration, cwd, and runtime metadata, redacts known
  sensitive values, produces a `decision.v0` result, policy-checks it, and saves
  a `run.v0` record under `.minerva/runs/`.
- If no local OpenAI-compatible provider is available, `observe` still records
  the command failure and returns a policy-blocked local fallback instead of
  requiring a remote LLM.
- `minerva diagnose <failure.json>` reads observation-shaped JSON and returns a
  structured Minerva decision.
- `minerva policy-check <decision.json>` validates a structured decision against
  the read-only policy boundary without executing tools.
- `minerva render-ci-summary <run-record>` and
  `minerva render-ci-artifact <run-record>` produce deterministic, redacted CI
  evidence for GitHub Actions summaries and JSON artifacts.
- `python3 -m minerva_kernel.eval_smoke` runs the deterministic M0 smoke eval.
- `minerva eval-report --format markdown` and
  `python3 -m minerva_kernel.eval_report --format markdown` generate the M1
  fixture-based metrics report.
- The current failure corpus contains 112 validated cases across 12 categories,
  with an M1 target of 15 cases per category.
- `models/cpu_model_candidates.json` records the CPU-local model candidate
  registry for sub-500M research without downloading weights or claiming
  benchmark results.

### What Changed

- Added M0 release readiness documentation covering the local CLI path,
  compile/unit/eval gates, demo path, redaction, policy boundaries, CI
  expectations, domain verification, known limitations, and go/no-go criteria.
- Added a clean-checkout local release dry-run guide for install, `doctor`,
  `observe`, run record inspection, `policy-check`, eval smoke, destructive
  command blocking, redaction checks, and final compile/unit gates.
- Added a CI and domain verification record that separates facts observable
  from a local checkout from release-owner confirmations for GitHub Actions,
  DNS, TLS, HTTPS content, and launch-blocker review.
- Added `scripts/check-release-readiness.py` for repeatable, bounded GitHub
  Actions and `minervakernel.com` DNS/TLS/HTTPS readiness evidence.
- Extended the release readiness checker with a no-download
  `local_install_backend` probe for `setuptools.build_meta` in the current
  interpreter or a fresh venv, so offline editable-install setup gaps are
  reported before `pip install --no-build-isolation -e .` fails.
- Added bounded auto-discovery for local install-backend readiness:
  `python3 scripts/check-release-readiness.py --skip-external --install-backend auto`
  reports the first local Python candidate that can import
  `setuptools.build_meta`, or a bounded failed-candidate list with the next
  action.
- Recorded full local release dry-run evidence for commit
  `ae8bc6bd773f9b745f5b8bbcb8c7b24518882ac7`, including install/smoke,
  `doctor`, `observe`, run-record inspection, `policy-check`, eval smoke,
  compile, unit tests, redaction, and policy-blocking evidence.
- Added M1 roadmap task seeds for CI renderers, integration examples, local
  model path, eval growth, and ecosystem documentation.
- Added deterministic CI renderer contracts for a GitHub Actions markdown
  summary and redacted `minerva_ci_run.v0` JSON artifact.
- Added ecosystem contribution guidance for taxonomy, policy, model, and
  adapter packs, including ownership boundaries and safety requirements.
- Added an M1 eval report showing current fixture metrics and remaining corpus
  gaps.
- Added a machine-readable CPU-local model candidate registry and a CPU model
  eval scoring contract covering JSON validity, failure label accuracy, safe
  recovery decisions, escalation quality, dangerous actions, latency, and
  fallback behavior.
- Fixed package metadata so editable install exposes the documented `minerva`
  console command, uses SPDX license metadata, and limits setuptools package
  discovery to `minerva_kernel`.
- Pinned the GitHub Actions CI smoke gate to Python 3.11, matching the
  known-good fresh-virtualenv release evidence instead of floating to unstable
  `3.x` runners.
- Recorded post-metadata-fix full local release dry-run evidence for commit
  `87dd7730a07f29c1b82de2ed937ad35c94db6e04`, including offline editable
  install, `minerva doctor` through the installed console command, `observe`,
  run-record inspection, `policy-check`, eval smoke, compile, 83 unit tests,
  redaction, and destructive-intent policy-blocking evidence.

### Safety Boundaries

- Minerva is read-only by default.
- Model output is not an authorization layer; policy must evaluate structured
  decisions before any consumer acts on them.
- Redaction happens before model input and before persisted records or CI
  artifacts are written.
- Shell execution, filesystem writes, destructive commands, credential access,
  unknown actions, low-confidence actions, high-risk actions, and unsupported
  escalation are blocked by default policy.
- CI output is diagnostic evidence only; the observed command exit code remains
  the CI gate.
- The minimum path must remain CPU-local and usable without a GPU, hosted
  model, cloud account, external service, or publish token.

### Non-Claims

- M0 does not auto-repair systems.
- M0 is not a full AIOps platform.
- M0 does not replace CI, monitoring, tests, incident platforms, or human
  review.
- M0 does not execute arbitrary model-generated shell commands.
- M0 does not require a remote LLM for the minimum local path.
- The smoke eval is a wiring and policy signal, not a production reliability
  benchmark.
- Redaction v0 is a basic safety layer, not a full DLP system.
- This draft does not claim remote GitHub Actions status, DNS, TLS, or
  `minervakernel.com` content have been verified for a release commit.

### Evidence Links

- [M0 release readiness checklist](docs/m0-release-readiness.md)
- [M0 local release dry-run guide](docs/m0-local-release-dry-run.md)
- [2026-05-08 post-metadata-fix local release dry-run evidence](.minerva/release-evidence/2026-05-08-post-metadata-fix-local-release-dry-run.md)
- [2026-05-08 local release dry-run evidence](.minerva/release-evidence/2026-05-08-local-release-dry-run.md)
- [M0 CI and domain verification record](docs/m0-ci-domain-verification-record.md)
- [M1 eval report](evals/m1_eval_report.md)
- [Ecosystem contribution guide](docs/ecosystem-contributions.md)
- [M1 roadmap task seeds](docs/m1-roadmap-task-seeds.md)
- [CI integration surface](docs/ci-integration-surface.md)
- [M0 launch blog post draft](docs/m0-launch-blog-post.md)
- [CPU-local model candidate registry](models/cpu_model_candidates.json)
- [CPU model eval scoring contract](docs/cpu-model-eval-scoring-contract.md)

### Next Tasks

- Confirm the GitHub Actions compile/test/eval gate is green for the exact
  release branch or announcement commit.
- Verify `minervakernel.com` DNS, TLS, and HTTPS content before any public
  announcement.
- Continue M1 CI renderer work so every branch publishes bounded Minerva
  summary and artifact evidence.
- Add SDK, agent, and CI integration examples that preserve redaction,
  policy-gating, and no-auto-repair behavior.
- Use the CPU-local candidate registry and scoring contract to run the first
  real local-model comparison through Ollama or a local GGUF adapter.
- Grow the corpus toward 15 redacted cases per required category while keeping
  dangerous-action checks at zero.
- Implement any missing contract-complete report fields before promoting a real
  local-model candidate.

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
- Added M1 roadmap task seeds for CI renderers, integration examples, local
  model path, eval growth, and ecosystem documentation.
- Added deterministic CI renderer contracts for a GitHub Actions markdown
  summary and redacted `minerva_ci_run.v0` JSON artifact.
- Added ecosystem contribution guidance for taxonomy, policy, model, and
  adapter packs, including ownership boundaries and safety requirements.
- Added an M1 eval report showing current fixture metrics and remaining corpus
  gaps.

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
- [M0 CI and domain verification record](docs/m0-ci-domain-verification-record.md)
- [M1 eval report](evals/m1_eval_report.md)
- [Ecosystem contribution guide](docs/ecosystem-contributions.md)
- [M1 roadmap task seeds](docs/m1-roadmap-task-seeds.md)
- [CI integration surface](docs/ci-integration-surface.md)
- [M0 launch blog post draft](docs/m0-launch-blog-post.md)

### Next Tasks

- Run the full local release dry run on the exact release commit and record the
  exact command outputs.
- Confirm the GitHub Actions compile/test/eval gate is green for the exact
  release branch or announcement commit.
- Verify `minervakernel.com` DNS, TLS, and HTTPS content before any public
  announcement.
- Continue M1 CI renderer work so every branch publishes bounded Minerva
  summary and artifact evidence.
- Add SDK, agent, and CI integration examples that preserve redaction,
  policy-gating, and no-auto-repair behavior.
- Document and evaluate the local model provider path, including Ollama or
  OpenAI-compatible local endpoints and CPU/GGUF candidates.
- Grow the corpus toward 15 redacted cases per required category while keeping
  dangerous-action checks at zero.
- Expand eval reporting with JSON validity, failure label accuracy, safe
  recovery decision rate, escalation quality, dangerous action rate, and latency
  for real local-model candidates.

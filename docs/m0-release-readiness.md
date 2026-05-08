# M0 Release Readiness Checklist

Current snapshot: 2026-05-08.

M0 is ready for public announcement only when the local CLI path, test and eval
evidence, safety boundaries, documentation, demo path, domain, and known
limitations all line up with the narrow product claim:

```text
Minerva M0 is a CPU-local failure interpreter that observes a command, structures
the failure state, policy-checks a bounded decision, and saves a local run record.
```

## Readiness Checklist

| Area | Go Criterion | Current Status | Evidence |
| --- | --- | --- | --- |
| CLI | `minerva observe -- <command>` captures command, cwd, stdout/stderr tails, exit code, duration, runtime metadata, decision, policy result, and saved run record. | Module entry path verified locally; editable install now exposes the documented `minerva` console command. | README quickstart, [M0 demo script](../examples/m0-demo-script.md), [install entrypoint test](../tests/test_install_entrypoint.py), and [local release dry-run evidence](../.minerva/release-evidence/2026-05-08-local-release-dry-run.md). |
| CLI | `minerva diagnose failure.json` can read an observation-shaped input and produce a structured decision. | Module entry path remains ready for local verification; console command path is unblocked by package metadata. | [Decision Schema v0](decision-schema-v0.md), [install entrypoint test](../tests/test_install_entrypoint.py), issue tracker scope, and [local release dry-run evidence](../.minerva/release-evidence/2026-05-08-local-release-dry-run.md). |
| Tests | `python3 -m compileall minerva_kernel` passes from a clean checkout. | Passed locally for commit `ae8bc6bd773f9b745f5b8bbcb8c7b24518882ac7` on 2026-05-08. | [Local release dry-run evidence](../.minerva/release-evidence/2026-05-08-local-release-dry-run.md). |
| Tests | `python3 -m unittest discover -s tests` passes from a clean checkout. | Passed locally for commit `ae8bc6bd773f9b745f5b8bbcb8c7b24518882ac7` on 2026-05-08. | 77 tests ran, OK; [local release dry-run evidence](../.minerva/release-evidence/2026-05-08-local-release-dry-run.md). |
| Eval | `python3 -m minerva_kernel.eval_smoke` passes and reports the expected deterministic M0 fixture result. | Passed locally for commit `ae8bc6bd773f9b745f5b8bbcb8c7b24518882ac7` on 2026-05-08. | 5/5 smoke cases passed, 0 failed; [local release dry-run evidence](../.minerva/release-evidence/2026-05-08-local-release-dry-run.md). |
| Security Boundaries | Default policy is read-only and fails closed on write tools, shell tools, destructive commands, credential access, unknown action labels, low confidence, higher risk, and escalation requests. | Documented as the M0 safety boundary. Must remain covered by tests. | [M0 launch draft](m0-launch-blog-post.md) and [Decision Schema v0](decision-schema-v0.md). |
| Redaction | Known sensitive values are redacted before model input and before saved observations, decisions, or run records are written. | Documented and represented in demo/eval expectations. Must remain covered by tests. | [Observation Schema v0](observation-schema-v0.md), [Decision Schema v0](decision-schema-v0.md), and [Failure case guide](failure-case-contributions.md). |
| CI | GitHub Actions compile/test/eval smoke gate is green on the release branch or announcement commit. | Not verified by this local document. | README CI gate and [M0 CI and domain verification record](m0-ci-domain-verification-record.md); remote CI must be checked before go. |
| Docs | README, launch draft, demo script, local dry-run guide, schemas, contribution guide, and release readiness doc are linked and internally consistent. | README and release readiness link the dry-run guide; launch, demo, schemas, and examples index remain linked. | README project docs, [M0 local release dry-run guide](m0-local-release-dry-run.md), and this file. |
| Demo | Demo command, saved run record inspection, policy-check step, eval smoke step, and safety checks can be run without a remote LLM. | Ready for local dry run. | [M0 demo script](../examples/m0-demo-script.md) and [M0 local release dry-run guide](m0-local-release-dry-run.md). |
| Domain | `minervakernel.com` resolves to the intended public project surface or announcement destination. | Not verified by this local document. | Release owner must verify DNS, TLS, and target content using the [M0 CI and domain verification record](m0-ci-domain-verification-record.md) before go. |
| Known Limitations | Public materials plainly say M0 is not auto-repair, not full AIOps, not a CI replacement, not a monitoring replacement, and not dependent on a remote LLM for minimum function. | Documented in launch and demo materials. | [M0 launch draft](m0-launch-blog-post.md) and [M0 demo script](../examples/m0-demo-script.md). |

## Local Release Verification

Run this from the repository root immediately before marking M0 ready:

```bash
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
python3 -m minerva_kernel.eval_smoke
```

Use the [M0 local release dry-run guide](m0-local-release-dry-run.md) for the
full clean-checkout command sequence, expected artifacts, run record inspection,
and safety checks.

Latest local evidence for commit `ae8bc6bd773f9b745f5b8bbcb8c7b24518882ac7`:
[2026-05-08 local release dry-run evidence](../.minerva/release-evidence/2026-05-08-local-release-dry-run.md).
It records passing compile, unit tests, eval smoke, run-record inspection,
policy checks, and redaction checks. That evidence recorded an install blocker:
editable install failed package metadata discovery, so the `minerva` console
script was unavailable and CLI checks used the module entry point from the
checkout. T35 fixed the package metadata after that snapshot; the install
entrypoint test now verifies an offline editable install in a fresh virtualenv
and confirms the distribution metadata exposes only `minerva_kernel` as a
top-level package.

Use the [M0 CI and domain verification record](m0-ci-domain-verification-record.md)
to record the remote GitHub Actions status, `minervakernel.com` DNS and TLS
target, HTTPS content check, and launch-blocker review without adding secrets to
the checkout.

For the repeatable CI/domain evidence pass, run:

```bash
python3 scripts/check-release-readiness.py --content-reviewed "Verified public Minerva page"
```

The script reports local checkout metadata, checks GitHub Actions for the
current commit when `gh` and network access are available, checks DNS/TLS/HTTPS
for `minervakernel.com`, and keeps output bounded for public issue comments. Use
`python3 scripts/check-release-readiness.py --skip-external` to verify the local
reporting path when external access is unavailable.

The public release decision must record the exact command output or CI links for
the release branch. A passing local run is necessary but not enough if remote CI
or the public domain are not verified.

## Current M0 Status

Completed or ready for release verification:

- Positioning is explicit: CPU-local failure interpreter for CI/CD, agents, and ops.
- README includes a quickstart for `minerva doctor`, `minerva observe --`, and eval smoke.
- README links the clean-checkout local release dry-run guide.
- Observation Schema v0 and Decision Schema v0 define the structured contracts.
- The default safety claim is read-only, policy-gated execution.
- Redaction expectations are documented for observations, decisions, run records, and contributed failure cases.
- Launch and demo drafts explain the narrow M0 claim and non-claims.
- CI expectations are documented in README.
- T31 local verification passed: `compileall`, 77 unit tests, eval smoke 5/5,
  run-record inspection, policy checks, and redaction checks for commit
  `ae8bc6bd773f9b745f5b8bbcb8c7b24518882ac7`.
- T35 package metadata verification fixed the editable-install blocker and
  exposes the documented `minerva` console command from a fresh virtualenv.

Remaining risks:

- The release decision still needs a fresh local compile/test run and eval smoke output if the release commit changes after this snapshot.
- Remote GitHub Actions status is not captured in this document and must be green before announcement.
- Domain resolution, TLS, and final public destination for `minervakernel.com` must be verified outside this local checkout.
- The smoke eval is a narrow wiring signal, not a benchmark or production reliability claim.
- Redaction v0 is a basic safety layer, not a full DLP system.
- M0 behavior without a local model provider intentionally demonstrates policy-blocked escalation rather than remote fallback.

Launch blockers:

- Any failing compile, unit test, or eval smoke command on the release commit.
- Any policy path that allows destructive commands, arbitrary model-generated shell execution, credential access, or unsafe escalation by default.
- Any demo step that requires a remote LLM for the minimum M0 path.
- Any recurrence of a package metadata issue that prevents the documented local install path
  from exposing the `minerva` console command.
- Any public doc that implies M0 auto-repairs systems, replaces CI/monitoring, or is a full AIOps platform.
- Any unredacted secret, credential, private log, full environment dump, or proprietary data in docs, examples, fixtures, or release materials.
- Missing or broken public domain target for `minervakernel.com`.
- Red remote CI on the release branch or announcement commit.

## Go / No-Go Criteria

Go when all of the following are true:

- Local release verification passes on the release commit.
- GitHub Actions is green for the same release commit.
- Demo dry run works from a clean checkout and produces a saved `.minerva/runs/` record.
- Public docs link to the release readiness checklist, launch draft, demo script, schemas, and known limitations.
- `minervakernel.com` resolves correctly and points to the intended public project surface.
- The announcement uses only the narrow M0 claim and preserves the explicit non-claims.

No-go if any of the following are true:

- Compile, unit tests, eval smoke, or CI fails.
- The demo requires cloud access, a remote LLM, write tools, or manual repair to show the minimum value.
- Policy permits an unsafe action by default or does not explain a block reason.
- Redaction leaves obvious secrets in model input or saved records.
- Domain or public docs are not ready.
- Known limitations are hidden, softened, or contradicted by launch copy.

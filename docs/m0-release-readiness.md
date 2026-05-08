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
| CLI | `minerva observe -- <command>` captures command, cwd, stdout/stderr tails, exit code, duration, runtime metadata, decision, policy result, and saved run record. | Module entry path and installed console command path verified locally; editable install exposes the documented `minerva` command. | README quickstart, [M0 demo script](../examples/m0-demo-script.md), [install entrypoint test](../tests/test_install_entrypoint.py), and [post-metadata-fix local release dry-run evidence](../.minerva/release-evidence/2026-05-08-post-metadata-fix-local-release-dry-run.md). |
| CLI | `minerva diagnose failure.json` can read an observation-shaped input and produce a structured decision. | Module entry path remains ready for local verification; console command path is unblocked by package metadata. | [Decision Schema v0](decision-schema-v0.md), [install entrypoint test](../tests/test_install_entrypoint.py), issue tracker scope, and [post-metadata-fix local release dry-run evidence](../.minerva/release-evidence/2026-05-08-post-metadata-fix-local-release-dry-run.md). |
| Tests | `python3 -m compileall minerva_kernel` passes from a clean checkout. | Passed locally for commit `87dd7730a07f29c1b82de2ed937ad35c94db6e04` on 2026-05-08. | [Post-metadata-fix local release dry-run evidence](../.minerva/release-evidence/2026-05-08-post-metadata-fix-local-release-dry-run.md). |
| Tests | `python3 -m unittest discover -s tests` passes from a clean checkout. | Passed locally for commit `87dd7730a07f29c1b82de2ed937ad35c94db6e04` on 2026-05-08. | 83 tests ran, OK; [post-metadata-fix local release dry-run evidence](../.minerva/release-evidence/2026-05-08-post-metadata-fix-local-release-dry-run.md). |
| Eval | `python3 -m minerva_kernel.eval_smoke` passes and reports the expected deterministic M0 fixture result. | Passed locally for commit `87dd7730a07f29c1b82de2ed937ad35c94db6e04` on 2026-05-08. | 5/5 smoke cases passed, 0 failed; [post-metadata-fix local release dry-run evidence](../.minerva/release-evidence/2026-05-08-post-metadata-fix-local-release-dry-run.md). |
| Security Boundaries | Default policy is read-only and fails closed on write tools, shell tools, destructive commands, credential access, unknown action labels, low confidence, higher risk, and escalation requests. | Documented as the M0 safety boundary. Must remain covered by tests. | [M0 launch draft](m0-launch-blog-post.md) and [Decision Schema v0](decision-schema-v0.md). |
| Redaction | Known sensitive values are redacted before model input and before saved observations, decisions, or run records are written. | Documented and represented in demo/eval expectations. Must remain covered by tests. | [Observation Schema v0](observation-schema-v0.md), [Decision Schema v0](decision-schema-v0.md), and [Failure case guide](failure-case-contributions.md). |
| CI | GitHub Actions compile/test/eval smoke gate is green on the release branch or announcement commit. | Not verified by this local document. | README CI gate and [M0 CI and domain verification record](m0-ci-domain-verification-record.md); remote CI must be checked before go. |
| Docs | README, launch draft, demo script, local dry-run guide, schemas, contribution guide, and release readiness doc are linked and internally consistent. | README and release readiness link the dry-run guide; launch, demo, schemas, and examples index remain linked. | README project docs, [M0 local release dry-run guide](m0-local-release-dry-run.md), and this file. |
| Demo | Demo command, saved run record inspection, policy-check step, eval smoke step, and safety checks can be run without a remote LLM. | Passed in the latest local dry run without a remote LLM. | [M0 demo script](../examples/m0-demo-script.md), [M0 local release dry-run guide](m0-local-release-dry-run.md), and [post-metadata-fix local release dry-run evidence](../.minerva/release-evidence/2026-05-08-post-metadata-fix-local-release-dry-run.md). |
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

Latest local evidence for commit `87dd7730a07f29c1b82de2ed937ad35c94db6e04`:
[2026-05-08 post-metadata-fix local release dry-run evidence](../.minerva/release-evidence/2026-05-08-post-metadata-fix-local-release-dry-run.md).
It records a successful offline editable install in a fresh Python 3.11
virtualenv using `python -m pip install --no-index --no-deps
--no-build-isolation -e .`, successful `minerva doctor` through the installed
console command, passing compile, 83 unit tests, eval smoke, run-record
inspection, policy checks, destructive-intent blocking, and redaction checks.
The previous package metadata blocker is fixed: installed distribution metadata
exposes only `minerva_kernel` as a top-level package. The dry run also recorded
that this host's Python 3.14 and Python 3.13 fresh virtualenvs do not seed
`setuptools`, so the no-build-isolation install path needs a local build backend
available before package metadata can be evaluated.

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
for `minervakernel.com`, checks that the local offline editable-install build
backend is importable, and keeps output bounded for public issue comments. Use
`python3 scripts/check-release-readiness.py --skip-external` to verify the local
checkout and current-interpreter install-backend path when external access is
unavailable.

To test the fresh-virtualenv prerequisite for the documented offline editable
install path without network access, run:

```bash
python3 scripts/check-release-readiness.py --skip-external --install-backend fresh-venv
```

The `local_install_backend` check passes only when `setuptools.build_meta` is
importable in the selected target. A failure means the interpreter or freshly
created venv does not have the local build backend required by
`python -m pip install --no-index --no-deps --no-build-isolation -e .`. The next
action is to use a local interpreter or venv that already includes
`setuptools.build_meta`, or seed it from an approved local wheel/cache before
rerunning; do not download dependencies as part of this readiness check. A
`skipped` status is acceptable only when separate install-backend evidence is
recorded.

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
- T36 post-metadata-fix local verification passed: offline editable install
  from a fresh Python 3.11 virtualenv exposed the documented `minerva` console
  command, `minerva doctor` passed, `compileall` passed, 83 unit tests passed,
  eval smoke passed 5/5, run-record inspection passed, policy checks passed,
  destructive-intent blocking passed, and redaction checks passed for commit
  `87dd7730a07f29c1b82de2ed937ad35c94db6e04`.

Remaining risks:

- The release decision still needs a fresh local compile/test run and eval smoke output if the release commit changes after this snapshot.
- Remote GitHub Actions status is not captured in this document and must be green before announcement.
- Domain resolution, TLS, and final public destination for `minervakernel.com` must be verified outside this local checkout.
- The no-build-isolation editable install path requires the fresh virtualenv to
  already include the local build backend; Python 3.14 and Python 3.13 venvs on
  the T36 host did not seed `setuptools`. The readiness checker now reports
  this as `local_install_backend` for the current interpreter or a fresh venv.
- The smoke eval is a narrow wiring signal, not a benchmark or production reliability claim.
- Redaction v0 is a basic safety layer, not a full DLP system.
- M0 behavior without a local model provider intentionally demonstrates policy-blocked escalation rather than remote fallback.

Launch blockers:

- Any failing compile, unit test, or eval smoke command on the release commit.
- Any policy path that allows destructive commands, arbitrary model-generated shell execution, credential access, or unsafe escalation by default.
- Any demo step that requires a remote LLM for the minimum M0 path.
- Any recurrence of a package metadata issue or release-environment build
  backend gap that prevents the documented local install path from exposing the
  `minerva` console command.
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

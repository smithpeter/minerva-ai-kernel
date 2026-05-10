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
| CI | GitHub Actions compile/test/eval smoke gate is green on the release branch or announcement commit. | Prepared to rerun on explicit Python 3.11, matching the known-good fresh-venv release evidence; remote status is not verified by this local document. | README CI gate, [CI integration recipe](integration-recipes.md), and [M0 CI and domain verification record](m0-ci-domain-verification-record.md); remote CI must be checked before go. |
| Docs | README, launch draft, demo script, local dry-run guide, schemas, contribution guide, public site artifact, Pages deployment workflow, domain cutover runbook, and release readiness doc are linked and internally consistent. | README and release readiness link the dry-run guide, static public artifact, GitHub Pages workflow, and domain cutover runbook; launch, demo, schemas, and examples index remain linked. | README project docs, [M0 local release dry-run guide](m0-local-release-dry-run.md), [public site artifact](../public-site/index.html), [GitHub Pages workflow](../.github/workflows/pages.yml), [domain cutover runbook](minervakernel-domain-cutover-runbook.md), and this file. |
| Demo | Demo command, saved run record inspection, policy-check step, eval smoke step, and safety checks can be run without a remote LLM. | Passed in the latest local dry run without a remote LLM. | [M0 demo script](../examples/m0-demo-script.md), [M0 local release dry-run guide](m0-local-release-dry-run.md), and [post-metadata-fix local release dry-run evidence](../.minerva/release-evidence/2026-05-08-post-metadata-fix-local-release-dry-run.md). |
| Domain | `minervakernel.com` resolves to the intended public project surface or announcement destination. | Blocked as of 2026-05-08: direct TLS diagnostics showed `CN=test.voxsign.net`, and a certificate-verification-bypassed fetch returned VoxSign title/content. A standalone Minerva page artifact and GitHub Pages workflow now exist, but the external custom-domain, DNS, TLS, and served-content checks still must be cut over and verified. | Release owner must serve [public-site/index.html](../public-site/index.html), optionally through the [GitHub Pages workflow](../.github/workflows/pages.yml), follow the [domain cutover runbook](minervakernel-domain-cutover-runbook.md), then verify DNS, TLS, Minerva brand signals, and target content using the [M0 CI and domain verification record](m0-ci-domain-verification-record.md) before go. |
| Known Limitations | Public materials plainly say M0 is not auto-repair, not full AIOps, not a CI replacement, not a monitoring replacement, and not dependent on a remote LLM for minimum function. | Documented in launch and demo materials. | [M0 launch draft](m0-launch-blog-post.md) and [M0 demo script](../examples/m0-demo-script.md). |

## Local Release Verification

Run this from the repository root immediately before marking M0 ready:

```bash
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
python3 -m minerva_kernel.eval_smoke
```

For the consolidated local operations view, run:

```bash
python3 scripts/release-ops-dashboard.py
```

The dashboard emits `release_ops_status.v0` and reports Plan-Eng-Review health,
AI-team queue status, eval smoke, CPU eval fixture status, local install
readiness, task queue completion, and worktree cleanliness. It uses
`scripts/check-release-readiness.py --skip-external --install-backend current`
for the readiness signal, so it does not call external services by default.
Dirty worktrees and pending task cards are release blockers in this dashboard.

If the only remaining blocker is a dirty worktree, generate the release handoff
inventory:

```bash
python3 scripts/release-handoff.py
```

The handoff emits `minerva.release_handoff.v0` with dashboard status,
changed-file categories, blockers, and next actions. It is a local review aid,
not a commit, deployment, or release publication step.

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

The intended static public page artifact is
[public-site/index.html](../public-site/index.html). It presents the Minerva AI
Kernel M0 claim, docs/GitHub links, safety non-claims, and CPU-local failure
interpreter positioning. Use the
[minervakernel.com domain cutover runbook](minervakernel-domain-cutover-runbook.md)
for nginx/static-host setup, certificate requirements, rollback, and readiness
verification commands. The artifact being present in the repository does not
mean the public domain is fixed; valid TLS and Minerva content must pass
readiness first.

The GitHub Pages deployment path is
[.github/workflows/pages.yml](../.github/workflows/pages.yml). It validates the
static artifact tests, uploads `public-site/`, and deploys it through GitHub
Pages. [public-site/CNAME](../public-site/CNAME) carries `minervakernel.com`
for the Pages artifact. A green Pages deployment still does not prove public
domain readiness; the release owner must verify GitHub Pages custom-domain
settings, DNS records, the managed certificate, HTTPS content, and the
Minerva/VoxSign brand guard before go.

For the repeatable CI/domain evidence pass, run:

```bash
python3 scripts/check-release-readiness.py --content-reviewed "Verified public Minerva page"
```

The script reports local checkout metadata, checks GitHub Actions for the
current commit when `gh` and network access are available, checks DNS/TLS/HTTPS
for `minervakernel.com`, fails HTTPS readiness when the page lacks Minerva
brand/content signals or includes VoxSign markers, checks that the local
offline editable-install build backend is importable in a bounded set of local
Python candidates, and keeps output bounded for public issue comments. Use
`python3 scripts/check-release-readiness.py --skip-external --install-backend auto`
to verify the local checkout and discover a local install-backend target when
external access is unavailable.

To test one exact target interpreter or the fresh-virtualenv prerequisite for
the documented offline editable install path without network access, run:

```bash
python3 scripts/check-release-readiness.py --skip-external --install-backend current --install-backend-python PYTHON
python3 scripts/check-release-readiness.py --skip-external --install-backend fresh-venv
```

The `local_install_backend` check passes only when `setuptools.build_meta` is
importable in the selected or discovered target. Auto mode reports the selected
passing candidate, or a bounded list of failed candidates. A failure means the
interpreter or freshly created venv does not have the local build backend
required by `python -m pip install --no-index --no-deps --no-build-isolation -e .`.
The next action is to use a local interpreter or venv that already includes
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
- README links the standalone public page artifact, GitHub Pages workflow, and
  domain cutover runbook.
- GitHub Pages workflow is present to validate and publish `public-site/`, with
  `public-site/CNAME` carrying `minervakernel.com`.
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
- Domain resolution, TLS, and final public destination for `minervakernel.com`
  are currently blocked until the external target serves a certificate valid
  for `minervakernel.com` and the intended Minerva public page artifact, not
  VoxSign.
- GitHub Pages custom-domain settings, DNS records, and managed certificate
  status still require external verification even if the Pages workflow is
  green.
- The no-build-isolation editable install path requires the fresh virtualenv to
  already include the local build backend; Python 3.14 and Python 3.13 venvs on
  the T36 host did not seed `setuptools`. The readiness checker now reports
  this as `local_install_backend` for the current interpreter or a fresh venv.
- The smoke eval is a narrow wiring signal, not a benchmark or production reliability claim.
- Redaction v0 is a basic safety layer, not a full DLP system.
- M0 behavior without a configured model provider uses the deterministic
  CPU-local baseline interpreter rather than remote fallback.

Launch blockers:

- Any failing compile, unit test, or eval smoke command on the release commit.
- Any policy path that allows destructive commands, arbitrary model-generated shell execution, credential access, or unsafe escalation by default.
- Any demo step that requires a remote LLM for the minimum M0 path.
- Any recurrence of a package metadata issue or release-environment build
  backend gap that prevents the documented local install path from exposing the
  `minerva` console command.
- Any public doc that implies M0 auto-repairs systems, replaces CI/monitoring, or is a full AIOps platform.
- Any unredacted secret, credential, private log, full environment dump, or proprietary data in docs, examples, fixtures, or release materials.
- Missing, broken, mismatched, or VoxSign-contaminated public domain target for
  `minervakernel.com`.
- Missing or failed Pages deployment evidence when GitHub Pages is the selected
  public-site path.
- Red remote CI on the release branch or announcement commit.

## Go / No-Go Criteria

Go when all of the following are true:

- Local release verification passes on the release commit.
- GitHub Actions is green for the same release commit.
- Demo dry run works from a clean checkout and produces a saved `.minerva/runs/` record.
- Public docs link to the release readiness checklist, launch draft, demo script, schemas, and known limitations.
- `minervakernel.com` resolves correctly, serves a certificate valid for
  `minervakernel.com`, and returns the intended Minerva public page.
- The served page matches or intentionally supersedes
  [public-site/index.html](../public-site/index.html) without weakening M0
  safety non-claims.
- If GitHub Pages is used, the Pages workflow is green for the release commit
  and its custom-domain settings, DNS records, and managed certificate are
  verified.
- The announcement uses only the narrow M0 claim and preserves the explicit non-claims.

No-go if any of the following are true:

- Compile, unit tests, eval smoke, or CI fails.
- The demo requires cloud access, a remote LLM, write tools, or manual repair to show the minimum value.
- Policy permits an unsafe action by default or does not explain a block reason.
- Redaction leaves obvious secrets in model input or saved records.
- Domain, including TLS certificate and Minerva page content, or public docs are
  not ready.
- Known limitations are hidden, softened, or contradicted by launch copy.

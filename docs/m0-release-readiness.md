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
| CLI | `minerva observe -- <command>` captures command, cwd, stdout/stderr tails, exit code, duration, runtime metadata, decision, policy result, and saved run record. | Ready for local release verification. | README quickstart and [M0 demo script](../examples/m0-demo-script.md). |
| CLI | `minerva diagnose failure.json` can read an observation-shaped input and produce a structured decision. | Ready for local release verification. | [Decision Schema v0](decision-schema-v0.md) and issue tracker scope. |
| Tests | `python3 -m compileall minerva_kernel` passes from a clean checkout. | Passed locally for this snapshot. Rerun on the release commit. | `Listing 'minerva_kernel'...` |
| Tests | `python3 -m unittest discover -s tests` passes from a clean checkout. | Passed locally for this snapshot. Rerun on the release commit. | 50 tests ran, OK. |
| Eval | `python3 -m minerva_kernel.eval_smoke` passes and reports the expected deterministic M0 fixture result. | Passed locally for this snapshot. Rerun on the release commit. | 5/5 smoke cases passed, 0 failed. |
| Security Boundaries | Default policy is read-only and fails closed on write tools, shell tools, destructive commands, credential access, unknown action labels, low confidence, higher risk, and escalation requests. | Documented as the M0 safety boundary. Must remain covered by tests. | [M0 launch draft](m0-launch-blog-post.md) and [Decision Schema v0](decision-schema-v0.md). |
| Redaction | Known sensitive values are redacted before model input and before saved observations, decisions, or run records are written. | Documented and represented in demo/eval expectations. Must remain covered by tests. | [Observation Schema v0](observation-schema-v0.md), [Decision Schema v0](decision-schema-v0.md), and [Failure case guide](failure-case-contributions.md). |
| CI | GitHub Actions compile/test/eval smoke gate is green on the release branch or announcement commit. | Not verified by this local document. | README CI gate; remote CI must be checked before go. |
| Docs | README, launch draft, demo script, schemas, contribution guide, and release readiness doc are linked and internally consistent. | Linked from README, launch draft, demo script, and examples index. | README project docs and this file. |
| Demo | Demo command, saved run record inspection, policy-check step, and eval smoke step can be run without a remote LLM. | Ready for local dry run. | [M0 demo script](../examples/m0-demo-script.md). |
| Domain | `minervakernel.com` resolves to the intended public project surface or announcement destination. | Not verified by this local document. | Release owner must verify DNS, TLS, and target content before go. |
| Known Limitations | Public materials plainly say M0 is not auto-repair, not full AIOps, not a CI replacement, not a monitoring replacement, and not dependent on a remote LLM for minimum function. | Documented in launch and demo materials. | [M0 launch draft](m0-launch-blog-post.md) and [M0 demo script](../examples/m0-demo-script.md). |

## Local Release Verification

Run this from the repository root immediately before marking M0 ready:

```bash
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
python3 -m minerva_kernel.eval_smoke
```

The public release decision must record the exact command output or CI links for
the release branch. A passing local run is necessary but not enough if remote CI
or the public domain are not verified.

## Current M0 Status

Completed or ready for release verification:

- Positioning is explicit: CPU-local failure interpreter for CI/CD, agents, and ops.
- README includes a quickstart for `minerva doctor`, `minerva observe --`, and eval smoke.
- Observation Schema v0 and Decision Schema v0 define the structured contracts.
- The default safety claim is read-only, policy-gated execution.
- Redaction expectations are documented for observations, decisions, run records, and contributed failure cases.
- Launch and demo drafts explain the narrow M0 claim and non-claims.
- CI expectations are documented in README.
- T15 local verification passed: `compileall`, 50 unit tests, and eval smoke
  5/5.

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

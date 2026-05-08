# M1 Roadmap Task Seeds

Date: 2026-05-08

M1 should turn M0 readiness into a repeatable product loop: CI can publish
useful Minerva evidence, integrations can adopt the structured decision
surface, the local model path can be evaluated honestly, the corpus can grow,
and ecosystem contributors can see where to plug in.

## M1 Objective

```text
Make Minerva useful in CI and agent workflows while preserving the M0 safety
claim: CPU-local minimum path, structured decisions, redaction before model
input, policy-gated actions, and read-only by default.
```

M1 is not an auto-repair release. It should improve diagnosis, summaries,
artifacts, adapter surfaces, model evaluation, and contribution paths without
executing model-selected actions automatically.

## Scope Boundaries

- Work only inside the Minerva repository.
- Do not use VoxSign state, tasks, tools, or docs.
- Keep integrations credential-free by default.
- Keep CI outputs redacted and bounded.
- Keep remote models optional; the minimum path must stay local and CPU-capable.
- Keep policy as the authorization layer for any proposed action.

## Roadmap Lanes

| Lane | M1 Result | Seed Tasks |
| --- | --- | --- |
| CI renderers | GitHub Actions can use `minerva observe --`, publish a deterministic markdown summary, and save a redacted `minerva_ci_run.v0` artifact without masking the observed command exit code. | T21, T22 |
| Integrations | Agent, SDK, and CI consumers have small examples that show how to feed observations into Minerva and consume decisions safely. | T23 |
| Local model path | The project has a measured path for Ollama/OpenAI-compatible local providers and a CPU/GGUF evaluation plan for sub-500M candidates. | T24 |
| Eval growth | The corpus grows beyond the M0 synthetic slice and reports model-relevant metrics, including safe recovery decision rate and dangerous action rate. | T25 |
| Ecosystem docs | Contributors can add taxonomy, policy, model, and adapter packs without guessing ownership boundaries or safety requirements. | T26 |

## Suggested T21+ Queue

Create or confirm the matching GitHub issues before assigning local workers.
The issue numbers below now refer to created GitHub issues and local task cards
ready for AI-team execution.

| Task | Lane | Proposed Issue | Title | Acceptance Signal |
| --- | --- | --- | --- | --- |
| T21 | Integration | #21 | Wire Minerva CI renderers into the GitHub Actions smoke workflow | CI uses `render-ci-summary` and `render-ci-artifact`; tests still pass. |
| T22 | Integration | #22 | Add CI renderer fixture and artifact contract regression coverage | Renderer output is stable for happy path, policy-blocked path, and redaction cases. |
| T23 | Integration | #23 | Add first SDK and agent integration examples | Examples show structured observation input, decision output, and policy-safe consumption. |
| T24 | Kernel / Research | #24 | Add local model provider path and CPU model eval plan | Local provider setup, fallback behavior, and sub-500M eval criteria are documented or smoke-tested. |
| T25 | Eval | #25 | Grow failure corpus and publish M1 eval metrics | Corpus categories grow, duplicate/schema checks hold, and safe recovery decision rate is reported. |
| T26 | Docs / Ecosystem | #26 | Add ecosystem contribution docs for packs and adapters | Taxonomy, policy, model, and adapter contribution surfaces are documented with safety boundaries. |

## Dependency Order

1. Start with T21 so CI evidence is visible on every branch.
2. Add T22 before broadening renderer behavior so artifact compatibility is
   protected.
3. Run T23 after the CI surface is stable, using the same observation and
   decision contracts.
4. Run T24 and T25 together only if write scopes are split between provider docs
   or code and eval corpus/reporting.
5. Run T26 after the integration and eval surfaces are clear enough for
   contributors to follow.

## M1 Done Signal

M1 is ready for a public update when:

- GitHub Actions publishes a bounded Minerva summary and artifact for the main
  compile/test/eval gate.
- Adapter examples preserve redaction, policy gating, and no auto-repair.
- Local model documentation names the exact candidate path and fallback behavior.
- Eval metrics include JSON validity, failure label accuracy, safe recovery
  decision rate, escalation quality, and dangerous action rate.
- Ecosystem docs explain how to contribute packs without using VoxSign or any
  unrelated repository state.

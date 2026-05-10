# AI-Team Stabilization Criteria

The AI-team loop should switch from scope expansion to stabilization when the
current vision queue has landed and the next useful work is review, evidence,
and release handoff.

## Stabilization Entry Criteria

Enter stabilization when all of the following are true:

- `.tasks/board.md` has no pending task cards for the active queue.
- Every completed task card has an `Output` section with verification commands.
- `bash scripts/check-plan-eng-review.sh` passes.
- `python3 -m unittest discover -s tests` passes.
- `python3 -m minerva_kernel.eval_smoke` passes.
- `python3 -m minerva_kernel.cpu_model_eval` returns `decision=promote` for
  the fixture harness.
- `python3 scripts/release-ops-dashboard.py --json --no-fail` has been run.
- `python3 scripts/release-handoff.py --json --no-fail` has been run when the
  worktree is dirty.

## Stabilization Behavior

During stabilization, the AI team should:

- fix failing checks before adding new scope
- keep new task cards limited to release blockers, evidence gaps, or explicit
  user requests
- avoid broad refactors
- avoid changing policy boundaries without a new Plan-Eng Review
- preserve dirty-worktree inventory through the release handoff artifact

## Exit To Release Review

The release owner can move from stabilization to release review when:

- `scripts/check-ai-team-stabilization.py` reports `ready=true`
- release dashboard has no failed checks except an intentionally reviewed dirty
  worktree during handoff
- release handoff identifies all changed-file categories and next actions
- no task card has an unresolved critical failure-mode gap

This does not publish a release, open a PR, or push commits. It only marks that
the local AI-team phase is ready for human review and packaging.

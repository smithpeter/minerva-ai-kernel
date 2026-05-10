# AI Team Timer Runbook

Minerva's local AI-team timer runs one bounded task tick every 30 minutes with a
systemd user timer on Linux.

Install or refresh the timer:

```bash
cd /home/ubuntu/projects/minerva-ai-kernel
bash scripts/install-ai-team-systemd-user.sh
```

Check timer state:

```bash
systemctl --user status minerva-ai-team-tick.timer
systemctl --user status minerva-ai-team-tick.service
journalctl --user -u minerva-ai-team-tick.service -n 100
```

Run one immediate tick:

```bash
systemctl --user start minerva-ai-team-tick.service
```

Disable the timer:

```bash
bash scripts/uninstall-ai-team-systemd-user.sh
```

Preflight:

```bash
bash scripts/ai-team-preflight.sh
bash scripts/check-plan-eng-review.sh
```

The preflight reports:

- repository root, branch, and head
- dirty worktree count
- pending task count
- `codex` and `claude` availability
- systemd timer state
- a final `ready=true|false` line with a reason

Required operating conditions:

- `MINERVA_PROJECT_ROOT` points to the Minerva checkout.
- The worktree is clean before the timer dispatches a worker.
- `.tasks/board.md` contains at least one pending task.
- `docs/plan-eng-review-workflow.md` is present; workers use it before
  substantial edits to separate planning, implementation, review, and shipping.
- `codex` or `claude` is available and authenticated for non-interactive use.
- Git identity and push permissions are configured if autopilot will finalize
  completed task cards.

Before seeding a new task, copy
[`docs/ai-team-task-template.md`](ai-team-task-template.md). The template keeps
the Plan-Eng Review block attached to the task card instead of relying on a
worker to remember the format from prose documentation.

If an executor is unavailable or unauthenticated, the service logs the pause and
exits successfully so the timer can retry on the next interval. This keeps the
timer healthy while making the worker credential problem visible in logs and
preflight output.

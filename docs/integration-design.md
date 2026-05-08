# Integration Design

Date: 2026-05-08

## Core Integration Problem

Minerva is only useful if it can receive enough runtime evidence.

Without logs, errors, exit codes, config hints, and tool context, Minerva cannot interpret failures.

Therefore integration design is a first-class product problem.

## Integration Principle

Minerva should meet users where failures already happen:

- terminal commands
- CI jobs
- build logs
- test reports
- deployment scripts
- agent tool calls
- observability webhooks
- local service logs

Users should not have to rewrite their systems to try Minerva.

## Integration Levels

### Level 0: Paste / File Diagnosis

Lowest-friction mode:

```bash
minerva diagnose --stderr stderr.log --stdout stdout.log --exit-code 1
minerva diagnose failure.json
```

Use when:

- user has a log file
- CI exports logs
- an agent has a captured tool error

Value:

- easiest onboarding
- no runtime wrapping
- useful for demos and docs

### Level 1: Command Wrapper

Primary developer mode:

```bash
minerva observe -- pytest
minerva observe -- npm test
minerva observe -- docker build .
minerva observe -- uv run pytest
```

Minerva captures:

- command
- cwd
- exit code
- stdout tail
- stderr tail
- duration
- environment summary
- available tools

It should not capture secrets by default.

### Level 2: CI Wrapper

CI mode:

```yaml
- run: minerva observe -- npm test
```

or post-failure analysis:

```yaml
- if: failure()
  run: minerva ci analyze --log build.log --junit junit.xml --output minerva.json
```

Outputs:

- JSON artifact
- Markdown summary
- PR comment
- failure label

The next credential-free GitHub Actions surface is documented in
[CI Integration Surface](ci-integration-surface.md). It defines a
`minerva observe --` wrapper pattern, a concise `$GITHUB_STEP_SUMMARY` markdown
format, and a redacted `minerva_ci_run.v0` JSON artifact shape.

### Level 3: SDK For Agents

Agent tool-call guard:

```python
from minerva_kernel import Minerva, Observation

try:
    result = tool.run(args)
except Exception as exc:
    observation = Observation.from_exception(tool="search", exc=exc)
    decision = Minerva().decide(observation)
```

This lets existing agent frameworks call Minerva when tools fail.

### Level 4: Local Daemon

Machine agent mode:

```text
minervad
```

Interfaces:

```text
POST /v1/decide
POST /v1/observe
GET /health
Unix socket
```

Use when:

- CI runner has repeated jobs
- ops node should keep local model warm
- platform wants local API

### Level 5: Platform Integration

For BlueKing-like systems:

```text
CI/CD platform
Job execution platform
Monitoring platform
CMDB/asset platform
Agent platform
```

Integration:

```text
platform -> Minerva API -> structured failure interpretation
```

## Observation Schema

Minimum:

```json
{
  "source": "cli",
  "command": "pytest",
  "cwd": "/repo",
  "exit_code": 1,
  "stdout_tail": "...",
  "stderr_tail": "...",
  "duration_ms": 5321,
  "timestamp": "2026-05-08T12:00:00Z"
}
```

Recommended:

```json
{
  "source": "ci",
  "command": "npm test",
  "cwd": "/workspace/app",
  "exit_code": 1,
  "stdout_tail": "...",
  "stderr_tail": "...",
  "duration_ms": 5321,
  "runtime": {
    "os": "linux",
    "arch": "x86_64",
    "python": "3.12.2",
    "node": "22.1.0",
    "docker": "26.1.0"
  },
  "ci": {
    "provider": "github_actions",
    "job": "test",
    "workflow": "ci",
    "branch": "main",
    "commit": "abc123"
  },
  "resources": {
    "cpu_load": 1.2,
    "memory_available_mb": 2048,
    "disk_available_mb": 12000
  },
  "policy": {
    "mode": "read_only",
    "network": "allowed",
    "writes": "forbidden"
  }
}
```

## Evidence Collection

Minerva should collect only enough evidence to diagnose.

Default evidence:

- stdout/stderr tail, not full logs
- exit code
- command
- cwd basename or repo-relative path
- tool versions
- selected config filenames, not full secret values

Optional evidence:

- full logs
- test reports
- package manifests
- service logs
- environment variables allowlist

Never collect by default:

- secrets
- tokens
- private keys
- full `.env`
- credential files
- SSH keys
- browser cookies
- cloud credentials

## Redaction

Redaction must happen before model input.

Default redactors:

- API keys
- bearer tokens
- passwords
- private keys
- AWS/GCP/Azure credentials
- GitHub tokens
- email addresses optional
- IP addresses optional

Output should include:

```json
{
  "redactions": {
    "count": 3,
    "types": ["token", "password"]
  }
}
```

## Log Size Strategy

Logs are often too long.

Use:

- head/tail extraction
- error-focused slicing
- stack trace extraction
- regex hints
- junit/test report parsing
- repeated-line compression
- max token budget

Do not blindly send whole logs to the model.

## Integration UX

The first-use experience should be:

```bash
pipx install minerva-ai-kernel
minerva doctor
minerva observe -- pytest
```

Expected output:

```text
Failure: missing_dependency
Action: inspect_dependencies
Confidence: 0.86
Risk: low
Escalate: false
```

With JSON:

```bash
minerva observe --json -- pytest
```

## CI Output UX

CI should produce:

- short summary
- JSON artifact
- optional markdown report
- optional PR comment

Example markdown:

```text
Minerva diagnosis: missing_dependency
Diagnostic action: inspect pyproject.toml and lockfile
Risk: low
Escalation: not required
Policy: allowed by read-only policy
```

The CI output contract should remain diagnostic only: no auto-repair, redaction
before model input, and policy-gated decisions.

## Agent Framework UX

Minerva should provide adapters that receive:

- tool name
- tool args summary
- exception
- stdout/stderr
- retry count
- allowed actions

Return:

- retry
- alternate tool
- inspect
- stop
- ask bigger model
- ask user

## Platform UX

Platforms should see Minerva as:

```text
failure interpretation service
```

Input:

- event/log/error

Output:

- normalized failure class
- action suggestion
- escalation target
- evidence summary
- policy decision

## Why This Matters

The easiest way for Minerva to fail is to require perfect integration before producing value.

Therefore the adoption ladder must be:

```text
paste/file -> command wrapper -> CI wrapper -> SDK -> daemon -> platform
```

Each step should provide value independently.

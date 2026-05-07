# Risks And User Value

Date: 2026-05-08

## Core Product Risk

The biggest risk is not model training failure.

The biggest risk is:

```text
users run Minerva, but do not feel it saved time or reduced uncertainty.
```

If users do not feel immediate value, the project fails even if the architecture is elegant.

## Top Failure Risks

### 1. Weak First Diagnosis

Risk:

```text
Minerva outputs a vague diagnosis that the user already knows.
```

Bad:

```text
Failure: test_failed
Action: check the logs
```

Good:

```text
Failure: missing_python_dependency
Evidence: ModuleNotFoundError: no module named 'pytest_asyncio'
Action: inspect_dependencies
Next: check pyproject.toml and lockfile for pytest-asyncio
```

### 2. No Evidence

Risk:

```text
The user does not trust the answer because Minerva does not show why.
```

Fix:

Always show:

- failure class
- evidence lines
- confidence
- suggested safe next action
- why it did not auto-execute

### 3. Too Much Noise

Risk:

```text
The output is longer than the original error.
```

Fix:

Default output must be short:

```text
Diagnosis
Evidence
Next safe action
Escalation
```

Detailed report only with:

```bash
--explain
```

### 4. Unsafe Suggestions

Risk:

```text
The tool suggests dangerous commands and loses user trust.
```

Fix:

Default to:

- read-only
- no destructive commands
- no credential access
- no writes unless explicitly enabled
- show policy block reason

### 5. Bad Integration UX

Risk:

```text
User must configure too much before seeing value.
```

Fix:

First use should be:

```bash
minerva observe -- pytest
```

No API key required.
No GPU required.
No config required.

### 6. Weak Model On Hard Cases

Risk:

```text
Small CPU model misdiagnoses complex failures.
```

Fix:

Minerva must be good at saying:

```text
I cannot classify this safely. Escalate.
```

Correct escalation is a success, not a failure.

### 7. No Feedback Loop

Risk:

```text
Every run is isolated, so the project does not improve.
```

Fix:

Every run can produce a local feedback artifact:

```text
.minerva/runs/<run-id>.json
```

Users can mark:

```text
correct
wrong
unsafe
helpful
not_helpful
```

## User Value Moments

Minerva must create obvious "value moments".

### Value Moment 1: It Extracts The Real Error

User sees:

```text
Minerva found the important error line out of 2,000 log lines.
```

### Value Moment 2: It Names The Failure

User sees:

```text
This is not just a failed build. It is a missing system library.
```

### Value Moment 3: It Suggests A Safe Next Step

User sees:

```text
Check package manifest before reinstalling everything.
```

### Value Moment 4: It Knows When To Stop

User sees:

```text
Minerva did not suggest a risky command. It asked for escalation.
```

### Value Moment 5: It Creates A Reusable Record

User sees:

```text
The failure is now structured and can be searched, grouped, and learned from.
```

## First-Run UX

Command:

```bash
minerva observe -- pytest
```

Output:

```text
Minerva diagnosis

Failure: missing_python_dependency
Confidence: 0.88
Evidence: ModuleNotFoundError: no module named 'pytest_asyncio'
Next: inspect_dependencies
Risk: low
Escalation: not required

Saved: .minerva/runs/2026-05-08T120000Z.json
```

With JSON:

```bash
minerva observe --json -- pytest
```

## Trust UX

Every diagnosis should include:

```text
because of these evidence lines
```

Not:

```text
because the model thinks so
```

## Product Promise

Do not promise:

```text
Minerva automatically fixes all failures.
```

Promise:

```text
Minerva finds the important failure signal, names the failure, suggests a safe next step, and escalates when unsure.
```

## Retention Loop

Users return if Minerva builds useful local memory:

```text
this project often fails due to missing env vars
this CI runner often has network timeouts
this dependency failure happened before
this test failure is new
```

This should remain local-first.

## Success Metric For User Value

Track:

```text
time_to_first_diagnosis
user_marked_helpful_rate
correct_failure_label_rate
dangerous_suggestion_rate
repeat_failure_recognition_rate
```

The most important early metric:

```text
user_marked_helpful_rate
```

Architecture does not matter if this is low.


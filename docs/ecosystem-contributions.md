# Ecosystem Contribution Guide

Minerva's ecosystem should grow through explicit, reviewable extension points:
taxonomy packs, policy packs, model packs, and optional adapters. Contributions
should make the local failure interpreter better without weakening the M0/M1
safety contract.

## Safety Contract

Every ecosystem contribution must preserve these claims:

- No auto-repair by default. Minerva output is diagnostic and advisory unless an
  explicit policy and executor path authorize more.
- Redaction before model input. Logs, commands, cwd values, runtime metadata,
  tool payloads, and persisted records must be redacted before any model sees
  them.
- Policy-gated decisions. Model output is never the authorization layer; policy
  must evaluate the structured decision before consumers act on it.
- CPU-local minimum path. The core path must still observe, classify, gate, and
  save useful evidence without a GPU, remote model, hosted service, or external
  account.
- Bounded evidence. Contributions should prefer compact examples, schema-shaped
  fixtures, and log tails over full logs, environment dumps, or private system
  state.
- Structured output. Packs and adapters should feed the existing observation,
  decision, policy, and artifact contracts instead of introducing free-form
  command execution.

## Ownership Boundaries

| Surface | Owner | Belongs Here | Does Not Belong Here |
| --- | --- | --- | --- |
| Core Minerva | Core maintainers | Schemas, redaction, policy runtime, CLI/SDK contracts, local provider fallback, deterministic eval harnesses | Product-specific credentials, hosted services, mandatory remote model dependencies, broad adapter dependencies |
| Community packs | Pack contributors and maintainers | Domain taxonomies, safe action labels, policy rules, model cards, eval fixtures, documentation | Unreviewed executor privileges, secrets, private logs, proprietary source, runtime changes that bypass core contracts |
| Optional adapters | Adapter contributors and maintainers | Thin mappings from external systems into Minerva `Observation` input and policy-checked `Decision` output | Required core dependencies, automatic repair loops, hidden network uploads, host-specific state inside the core package |

Core Minerva should remain small and local-first. Optional integrations should
stay installable and removable without changing the minimum runtime. Community
packs can extend knowledge and defaults, but they do not own the authorization
boundary; policy and executor behavior remain explicit core contracts.

## Taxonomy Packs

Taxonomy packs teach Minerva about failure domains such as Python, Node, Docker,
Kubernetes, CI, networking, model APIs, schema validation, permissions, or edge
devices.

Expected contents:

- Pack manifest with `id`, `version`, `domain`, `maintainers`, license, and
  compatible Minerva schema versions.
- Failure labels with concise definitions and examples of matching signals.
- Safe action labels that map to bounded diagnostic or inspect-first actions.
- Redacted examples that follow the failure case contribution format.
- Negative examples for lookalike failures that should not use the label.
- Risk notes that name actions Minerva must not take automatically.
- Eval fixtures that validate duplicate IDs, schema shape, label mapping, and
  expected safe action behavior.

Safety requirements:

- Labels describe failure shape; they must not smuggle shell commands or repair
  scripts into the taxonomy.
- Examples must remove secrets, private logs, full environment dumps, customer
  data, and proprietary source.
- Safe actions should be read-only or narrowly diagnostic unless a separate
  reviewed policy and executor path exists.
- A taxonomy pack must not widen policy by itself. It can suggest action labels;
  policy decides whether those labels are allowed.
- Ambiguous or high-risk labels should prefer escalation or human review over
  confident repair.

## Policy Packs

Policy packs define which structured decisions are allowed in a given operating
mode, such as read-only, CI-safe, local-dev, enterprise-strict, edge-offline, or
human-approval.

Expected contents:

- Pack manifest with `id`, `version`, owner, intended environment, and supported
  decision schema versions.
- Allow and deny rules for action labels, risk levels, escalation states, and
  evidence requirements.
- Human approval requirements for write, destructive, network, credential, or
  deployment-adjacent actions.
- Default-deny behavior for unknown actions, unknown risk levels, invalid
  schema output, and missing evidence.
- Tests that show representative allowed decisions and blocked decisions.
- Audit notes explaining why each non-default allowance is safe for the target
  environment.

Safety requirements:

- Policy packs must fail closed.
- Policy packs must not bypass the core policy runtime or execute tools
  directly.
- A policy pack cannot make auto-repair the default. Any non-read-only action
  needs an explicit reviewed executor path and approval model.
- Shell execution, filesystem writes, package installs, deployment actions,
  credential access, and outbound network calls must remain denied unless
  clearly scoped and separately reviewed.
- Blocked decisions should still preserve the reason so adapters and CI
  summaries can explain what happened.

## Model Packs

Model packs describe a local or optional remote model path for Minerva's narrow
controller task: classify failures, choose safe action labels, produce valid
structured decisions, and escalate when confidence or safety is insufficient.

Expected contents:

- Model card with model name, source, license, parameter count, quantization,
  expected hardware, memory footprint, and CPU latency notes.
- Provider configuration for a local OpenAI-compatible endpoint, GGUF runtime,
  or other supported local provider.
- Prompt or instruction template that requests only the supported structured
  decision schema.
- Eval report with schema-valid rate, expected label/action rate, dangerous
  action rate, policy-block rate, redaction coverage, and fallback behavior.
- Checksums or provenance notes for weights when weights are redistributed.
- Clear statement of whether the pack includes weights, references external
  weights, or only documents configuration.

Safety requirements:

- The CPU-local minimum path must remain usable without this model pack.
- Remote models can be optional escalation targets, but they must not be
  required for `minerva observe --` or the minimum local path.
- Model input must be redacted before inference. A model pack must not ask
  adapters or users to send raw logs, secrets, or full environments.
- Structured output must validate against the decision schema without adapter
  auto-repair or hidden free-form parsing.
- Eval reports should identify dangerous outputs, including arbitrary shell
  commands, write actions, credential access, remote upload requests, or
  unsupported action labels.
- If the model is unavailable, the runtime should return a structured fallback
  decision that policy can gate.

## Adapters

Adapters connect Minerva to CI systems, agent frameworks, model gateways,
editors, incident tools, or device runtimes. They should be optional integration
packages or examples, not mandatory core dependencies.

Expected contents:

- Adapter manifest or README with target system, supported versions, dependency
  list, and Minerva compatibility.
- Mapping from host failure state into Minerva `Observation` fields.
- Redaction boundary that runs before model input and before persisted adapter
  artifacts.
- Decision consumption path that checks `policy_decision.allowed` before any
  host action is taken.
- Failure behavior for unavailable Minerva runtime, unavailable local model,
  invalid decisions, policy blocks, and host API errors.
- Tests or examples for success, failure, redaction, policy-allowed, and
  policy-blocked paths.

Safety requirements:

- Adapters must not execute Minerva-proposed actions automatically by default.
- Adapters must not mask the host command or job status. In CI, the observed
  command remains the gate.
- Adapters must not upload raw logs or private state to hosted services unless
  the user explicitly configured that path outside the minimum runtime.
- Adapters should depend on stable CLI, SDK, or artifact contracts rather than
  importing internal modules.
- Optional dependencies must stay optional so core Minerva remains CPU-local and
  lightweight.
- Adapter summaries should show policy status and block reasons, not only the
  model's proposed action.

## Contribution Checklist

Before submitting a pack or adapter, confirm:

- The contribution names the surface it extends: taxonomy, policy, model, or
  adapter.
- The manifest or README states ownership, version, license, compatibility, and
  operating assumptions.
- Examples are compact and redacted.
- Tests or eval fixtures cover the expected positive path and at least one
  blocked or unsafe path.
- Policy remains the authorization layer.
- No remote model, hosted account, token, or external service is required for
  Minerva's minimum local path.
- No auto-repair behavior is enabled by default.
- Links to related docs are included when relevant:
  [failure case contributions](failure-case-contributions.md),
  [CI integration surface](ci-integration-surface.md), and
  [model strategy](model-strategy.md).

## Review Checklist

Maintainers should ask these questions during review:

- Does this improve classification, policy clarity, model evaluation, or
  integration ergonomics without expanding hidden runtime authority?
- Does every action remain structured and policy-gated?
- Are secrets, private logs, proprietary source, customer data, and unnecessary
  system state absent?
- Is the CPU-local minimum path unchanged?
- Are risky behaviors denied, escalated, or marked for human approval?
- Can the contribution be removed without breaking core Minerva?

If a contribution needs new executor authority, treat it as a separate core
design review. It should not land as a pack-only or adapter-only change.

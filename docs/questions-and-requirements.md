# Questions And Product Requirements

Date: 2026-05-08

This document records the core questions raised during the project discussion and converts them into product requirements.

The questions are not side notes. They represent the founder's real concerns and should guide the product.

## Q1: What is the original research idea?

Question:

```text
Can we build a scheduler whose kernel always has access to an LLM,
and whose code can always call an LLM to manage tools, resources, programs, networks, and failures?
```

Answer:

Yes, but the robust claim must be reframed.

The system cannot guarantee one LLM is always correct or online. It can guarantee an architecture with:

- minimum local LLM path
- fallback model tiers
- health checks
- safe structured actions
- escalation
- policy-controlled execution

Product requirement:

```text
Minerva must preserve a minimum local reasoning path even when remote models, tools, or networks fail.
```

## Q2: What is unique about this project?

Question:

```text
What is unique? Why is it valuable?
```

Answer:

The uniqueness is not another agent framework. It is:

```text
smallest local LLM as a runtime control kernel for failure interpretation and safe recovery routing
```

Product requirement:

```text
Do not position Minerva as a general agent framework. Position it as a CPU-local AI reliability kernel / failure interpreter.
```

## Q3: What does red-blue analysis say?

Question:

```text
Using red-blue thinking, what is the value and what are the weaknesses?
```

Answer:

Blue team:

- AI systems need a reliability layer.
- Small models are enough for classification/routing.
- CPU-only local fallback is valuable.

Red team:

- small models may be weak
- existing AIOps/agent systems exist
- LLM-driven execution is risky
- vague claims are not enough

Product requirement:

```text
Minerva must be eval-led, policy-gated, narrow, and CPU-local.
```

## Q4: How should the project be branded?

Question:

```text
How should this be named and branded?
```

Answer:

Use:

```text
Minerva
minerva-ai-kernel
AI Reliability Kernel
Minimum Local LLM Control Kernel
```

Avoid:

- Fallback Kernel as primary brand
- Sentinel Kernel
- Aegis Kernel
- Agent OS

Product requirement:

```text
Use Minerva as the brand and minerva-ai-kernel as the project/repository name.
```

## Q5: How can AI teams work on it without conflicting with VoxSign?

Question:

```text
If an AI team develops this, how do we avoid conflicts with VoxSign?
```

Answer:

Use separate directory, separate repository, separate namespace, and external integration only.

Product requirement:

```text
Minerva must be developed outside VoxSign, with no direct dependency on VoxSign modules.
```

## Q6: Is distillation needed?

Question:

```text
Should the project use distillation? Can RTX 3090 support this?
```

Answer:

Distillation may be needed, but not first.

Sequence:

```text
benchmark -> corpus -> teacher labels -> SFT/QLoRA -> optional preference training
```

RTX 3090 is enough for 135M/360M/490M fine-tuning and QLoRA.

Product requirement:

```text
Build Failure Corpus and Failure Bench before model training. Use distillation only after baseline evaluation proves the gap.
```

## Q7: Can the final model be under 500M and CPU-only?

Question:

```text
Can this run under 500M parameters, even on CPU?
```

Answer:

Yes, if the task is constrained.

The model cannot be a general engineer. It must be:

```text
classifier + router + escalator
```

Candidate models:

- Qwen2.5-Coder-0.5B-Instruct
- Qwen2.5-0.5B-Instruct
- SmolLM2-360M-Instruct
- Granite 4.0 350M
- SmolLM2-135M-Instruct for nano experiments

Product requirement:

```text
Minerva's minimum runtime must be CPU-only and sub-500M, using finite actions and structured outputs.
```

## Q8: What is the deeper meaning of the project?

Question:

```text
Is this a new kind of interpreter for the AI era?
```

Answer:

Yes. Traditional interpreters interpret code. Minerva interprets runtime state.

Core mapping:

```text
runtime failure state -> structured safe action
```

Product requirement:

```text
Design Observation Schema, Instruction Set, Policy Runtime, Failure Taxonomy, and Safe Action Library as the equivalents of language/runtime components.
```

## Q9: Can the system self-optimize and schedule computer resources?

Question:

```text
Can the system self-optimize and really schedule compute, tools, models, and resources?
```

Answer:

Yes, but only within bounded mechanisms.

Allowed:

- improve corpus
- tune routing thresholds
- improve policies
- learn action outcomes
- distill better small models

Not allowed by default:

- self-authorize permissions
- bypass policy
- execute arbitrary commands
- silently modify core runtime

Product requirement:

```text
Self-improvement must be evidence-based, not self-authorizing.
```

## Q10: Why can this founder do it? Why have others not done it?

Question:

```text
Why can I do this, and why has no one else focused on it?
```

Answer:

Most teams chase larger models, stronger agents, or full platforms. This project focuses on minimum local intelligence under failure.

The founder's advantage is direct exposure to:

- local AI
- edge runtime
- voice/action systems
- agent tools
- ops pain
- model/tool failures
- low-resource constraints

Product requirement:

```text
Keep the project grounded in real failure cases, not abstract agent architecture.
```

## Q11: Is AIOps a natural direction?

Question:

```text
Since configuration, CI/CD, and ops consume so much time, can this become a foundation AIOps agent like BlueKing-style agents?
```

Answer:

Yes, but Minerva should not become a full AIOps platform first.

It should become:

```text
the CPU-local failure interpretation layer for CI/CD, agents, and ops platforms
```

Product requirement:

```text
First vertical should be CI/CD failure triage, then ops agent mode, then platform integration.
```

## Q12: How will users integrate it?

Question:

```text
If logs and errors are not easy to capture, how will users feel value?
```

Answer:

Adoption must follow a ladder:

```text
paste/file -> command wrapper -> CI wrapper -> SDK -> daemon -> platform
```

Product requirement:

```text
The first integration must be `minerva observe -- <command>`, with no API key, no GPU, and no configuration required.
```

## Q13: What is the biggest product risk?

Question:

```text
If users cannot feel value, how does the project avoid failure?
```

Answer:

The biggest risk is not model training. It is weak user value.

Minerva must create value moments:

- extract key error lines
- name failure precisely
- show evidence
- suggest safe next action
- know when to escalate
- save structured record

Product requirement:

```text
First-run UX must make the user feel Minerva saved time or reduced uncertainty.
```

## Q14: How does this reconnect to LLM robustness?

Question:

```text
The original idea was that LLM must be robust. How does this project relate?
```

Answer:

Minerva is the runtime mechanism for LLM robustness.

Robustness layers:

- availability robustness
- output robustness
- tool robustness
- model robustness
- repair robustness

Product requirement:

```text
Minerva must treat model failures, tool failures, and environment failures as first-class runtime observations.
```

## Q15: How should auto-repair work?

Question:

```text
Can this automatically repair?
```

Answer:

Yes, but staged:

```text
diagnose -> recommend -> safe inspect -> proposed patch -> approved repair -> policy-autonomous repair
```

Product requirement:

```text
Early Minerva should stop at diagnosis, recommendation, safe inspection, and proposed patches. Autonomous repair must require policy approval.
```

## Q16: What is the final strategy?

Question:

```text
What should the whole project become?
```

Answer:

Start narrow:

```text
CPU-local CI/CD and command failure interpreter
```

Then grow into:

```text
local AI reliability layer for agents, tools, CI/CD, and ops platforms
```

Long-term:

```text
AI-era runtime state interpreter
```

Product requirement:

```text
Roadmap must move from local command failure to CI/CD to agent tool failures to ops agent mode to platform integration.
```

## Consolidated Product Requirements

1. CPU-only minimum runtime.
2. Sub-500M model target.
3. GGUF deployment.
4. No remote LLM required for minimum function.
5. Observation Schema.
6. Finite Minerva Instruction Set.
7. Policy-gated execution.
8. Safe Action Library.
9. Failure Taxonomy.
10. Failure Corpus.
11. Failure Bench.
12. Command wrapper first UX.
13. CI/CD first vertical.
14. Agent tool-failure SDK.
15. Local daemon later.
16. Evidence-first diagnosis.
17. Redaction before model input.
18. Read-only default.
19. Staged auto-repair.
20. Self-improvement through evidence only.


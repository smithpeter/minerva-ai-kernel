# Related Work Scan

Date: 2026-05-08

## Scope And Limitation

This scan searches public web, X-indexed posts, GitHub repositories, project docs, and papers for systems similar to an always-available LLM scheduler kernel.

Important limitation: public internet search cannot prove 100% coverage of all X posts, private repositories, deleted posts, unindexed code, or every file in large GitHub repositories. The practical target is high-recall discovery through overlapping search terms and source classes.

Search themes used:

- LLM scheduler
- AI agent operating system
- LLM OS
- local-first AI agent
- local LLM routing
- model fallback
- agent runtime
- tool router
- distributed agent scheduler
- self-healing LLM agent
- OpenAI-compatible LLM gateway
- always-on agent
- X.com posts about OpenClaw, Hermes, local-first agents, Claws

## Closest Matches

### 1. AIOS

Source:

- https://github.com/agiresearch/AIOS
- https://huggingface.co/papers/2403.16971
- https://huggingface.co/papers/2312.03815

Summary:

AIOS is the closest academic match. It explicitly frames the system as an AI Agent Operating System. Its kernel manages LLM, memory, storage, tools, scheduling, context switching, and access control. It supports local kernel and remote kernel modes.

Similarity to this project:

- Very high for OS/kernel framing.
- Very high for scheduling, context management, memory management, tool management, and access control.
- Medium for local-first tiny model fallback. AIOS supports Ollama/vLLM/HuggingFace, but the central research is agent OS resource management, not specifically a minimum always-on scheduler brain.

Key gap:

AIOS focuses on managing agent requests over LLM resources. Our direction focuses on a smallest local LLM as a persistent control kernel that watches code/tool/environment failure and escalates through model tiers.

### 2. Agent Control Plane

Source:

- https://github.com/humanlayer/agentcontrolplane

Summary:

ACP is a distributed agent scheduler built on Kubernetes. It models LLMs, Agents, Tools, Tasks, and ToolCalls as Kubernetes resources. It provides durable agent execution, checkpointing around tool calls, dynamic replanning, observable control loops, human approval, and MCP support.

Similarity:

- Very high for scheduling, durable execution, tool calls, and observable control loops.
- High for human-in-the-loop escalation.
- Medium for local-first operation; the default docs start with OpenAI, though other providers are supported.

Key gap:

ACP is infrastructure-first and Kubernetes-native. Our kernel is smaller, local-first, and centered on minimal model availability and code/environment diagnosis.

### 3. AGEniX

Source:

- https://agenix.sh/

Summary:

AGEniX is a local-first agentic Unix platform. It splits planning, queueing, and worker execution. Workers execute deterministic plans and do not have LLM capabilities. It supports local LLMs through Ollama/llama.cpp and emphasizes zero-trust architecture.

Similarity:

- Very high for local-first design.
- Very high for separating LLM planning from deterministic execution.
- High for safe tool execution.

Key gap:

AGEniX seems more like a secure agentic Unix execution platform. Our research is more specifically about the LLM availability hierarchy, smallest local controller, and failure-observation loop.

### 4. AgentVM

Source:

- https://llmhut.com/

Summary:

AgentVM describes itself as an operating system for AI agents. It provides process management, memory bus, tool routing, message passing, and scheduling. The architecture has five modules: process manager, memory bus, tool router, message broker, and scheduler.

Similarity:

- Very high for agent runtime/kernel concepts.
- High for tool routing and scheduling.
- High for crash recovery/checkpointing direction.

Key gap:

AgentVM is a general multi-agent runtime. Our proposed scheduler is more explicitly a model-router plus failure-diagnosis kernel with minimal local LLM fallback.

### 5. OpenClaw

Sources:

- https://docs.openclaw.ai/concepts/multi-agent
- https://openclawlab.com/en/docs/providers/local-models/
- https://github.com/openclaw/openclaw/blob/main/docs/providers/ollama.md
- X indexed examples: https://x.com/Techmeme/status/2025039183182532756 and https://x.com/martyryze/status/2026326256162054243

Summary:

OpenClaw is a local/self-hosted AI agent platform with Gateway, multiple messaging channels, skills, memory, model providers, local models, and multi-agent routing. Its docs explicitly support a pattern of local primary model plus remote fallback.

Similarity:

- Very high for local-first agent runtime.
- High for multi-model routing and fallback.
- High for always-on personal agent patterns.
- Medium for scheduler-kernel rigor.

Key gap:

OpenClaw is a full personal automation framework. Our research can be narrower and more formal: model health, structured action schema, policy validation, minimal controller model, and failure-loop evaluation.

### 6. Hermes / Local-First Swarm Discussions On X

Sources:

- https://x.com/glitch_/status/2033175616485286254
- https://x.com/martyryze/status/2026326256162054243

Summary:

Indexed X posts describe local-first multi-agent systems, model routing, persistent memory, execution sandboxing, subagent isolation, cron-like continuous operation, and cost-aware routing. These posts are highly aligned with the “always-on local AI operator” direction.

Similarity:

- High for local-first operation.
- High for multi-model routing.
- High for persistent memory and autonomous loops.

Key gap:

These are mostly product/architecture discussions, not a minimal scheduler kernel specification or benchmarked codebase.

## Important Adjacent Projects

### LiteLLM

Source:

- https://github.com/BerriAI/litellm

Summary:

LiteLLM is an open-source AI Gateway for 100+ LLMs. It provides a unified OpenAI-format interface, proxy mode, virtual keys, spend tracking, guardrails, load balancing, retries, fallback logic, and observability.

Relevance:

Strong candidate for the LLM Router layer, but not an agent scheduler by itself.

### Portkey AI Gateway

Source:

- https://github.com/Portkey-AI/gateway
- https://portkey.ai/docs/product/ai-gateway/fallbacks

Summary:

Portkey provides a lightweight AI gateway with routing, retries, fallbacks, conditional routing, caching, guardrails, and MCP gateway support.

Relevance:

Useful reference for production-grade fallback, retries, circuit breaking, and routing configuration.

### LLMRouter

Source:

- https://github.com/ulab-uiuc/LLMRouter

Summary:

LLMRouter is an open-source library for choosing the best LLM based on task complexity, cost, and performance. It includes many routing model families.

Relevance:

Good research source for learned model selection. It does not provide tool execution or environment-repair loops.

### Babber

Source:

- https://babber.app/

Summary:

Babber is a self-hosted, local-LLM autonomous agent platform. It uses Ollama or OpenAI-compatible APIs, includes multiple agents, skills, long-term memory, MongoDB, Redis, ChromaDB, and Docker.

Relevance:

Close for local autonomous agent platform. Less focused on minimal scheduler kernel and structured system repair.

### AutoGen

Source:

- https://github.com/microsoft/autogen

Summary:

AutoGen is a multi-agent programming framework with message passing, local/distributed runtime, tools, and code execution. It is now in maintenance mode, with Microsoft Agent Framework as successor.

Relevance:

Important historical multi-agent orchestration reference, less aligned with always-on local scheduler kernel.

### LangGraph

Source:

- https://github.com/langchain-ai/langgraph

Summary:

LangGraph is a low-level orchestration framework for long-running stateful agents with durable execution and resumption after failures.

Relevance:

Strong execution graph/checkpointing reference, but not specifically a local LLM availability kernel.

### CrewAI

Source:

- https://github.com/crewAIInc/crewAI

Summary:

CrewAI is a multi-agent orchestration framework with autonomous agents, tools, planning, memory, and flows.

Relevance:

Useful for workflow orchestration, less close to OS-style scheduling and model health/fallback.

### Semantic Kernel

Source:

- https://github.com/microsoft/semantic-kernel

Summary:

Semantic Kernel is a model-agnostic SDK for building and orchestrating agents and multi-agent systems with tools/plugins, memory, and planning.

Relevance:

Good SDK/framework reference, but not a scheduler kernel.

## Papers And Concepts To Track

### LLM Agent Operating System

Source:

- https://huggingface.co/papers/2403.16971

Directly relevant. The abstract highlights resource allocation, context switching, concurrent execution, tool services, and access control for agents.

### LLM As OS, Agents As Apps

Source:

- https://huggingface.co/papers/2312.03815

Conceptual predecessor to AIOS. Important framing source.

### MemGPT

Source:

- https://arxiv.gg/paper/2310.08560

Relevant for OS-inspired context/memory management, not execution scheduling.

### MemoryOS / MemOS

Sources:

- https://arxiv.gg/abs/2506.06326
- https://www.sciencestack.ai/paper/2507.03724

Relevant for treating memory as an OS resource.

### AgentRM

Source:

- https://gist.science/paper/2603.13110

OS-inspired resource manager using queue scheduling and context lifecycle management for LLM agent systems.

### SchedCP / Agentic OS For Linux Schedulers

Source:

- https://www.researchgate.net/publication/395214569_Towards_Agentic_OS_An_LLM_Agent_Framework_for_Linux_Schedulers

Relevant because it applies LLM agents to OS scheduler optimization, but it is closer to optimizing Linux schedulers than creating a general LLM scheduler kernel.

## Similarity Ranking

| Rank | Project | Similarity | Why |
|---:|---|---|---|
| 1 | AIOS | Very high | Explicit AI agent OS/kernel with scheduling, memory, tools, access control |
| 2 | AGEniX | Very high | Local-first, LLM planner, deterministic workers, secure execution |
| 3 | ACP | High | Distributed agent scheduler, durable tool calls, control loops, MCP |
| 4 | AgentVM | High | Agent OS/runtime with process, memory, tools, messages, scheduler |
| 5 | OpenClaw | High | Local-first always-on agents, skills, memory, routing, model fallback |
| 6 | LiteLLM / Portkey | Medium-high | Excellent model routing/fallback layer, but not full scheduler |
| 7 | LLMRouter | Medium | Model selection research, not execution kernel |
| 8 | LangGraph / AutoGen / CrewAI / Semantic Kernel | Medium | Agent orchestration frameworks, not always-on model kernel |

## Gap Analysis

The proposed project is still distinct if it focuses on:

1. Smallest always-available local model as the baseline scheduler brain.
2. Unified code-callable LLM interface with health checks and fallback tiers.
3. Structured action schema as the only execution contract.
4. Policy engine between LLM proposal and tool execution.
5. Environment-observation loop for code errors, network errors, resource errors, and tool failures.
6. Explicit escalation rules from tiny local model to larger local model to remote model to human.
7. Benchmarks for tiny-model scheduler competence, not general chat/coding competence.

## Recommendation

Do not build a full agent framework first. Build the missing kernel slice:

```text
LLM health router + tiny local controller + structured action schema + policy validator + execution observer + escalation ladder
```

Use existing systems as references:

- AIOS for kernel abstractions.
- AGEniX for zero-trust planner/worker separation.
- ACP for durable task/tool-call state.
- LiteLLM or Portkey for model gateway patterns.
- OpenClaw/Hermes discussions for local-first always-on product behavior.

## Next Research Step

For true code-level due diligence, clone and inspect the top repositories:

1. `agiresearch/AIOS`
2. `humanlayer/agentcontrolplane`
3. `openclaw/openclaw`
4. `BerriAI/litellm`
5. `Portkey-AI/gateway`
6. `ulab-uiuc/LLMRouter`
7. `langchain-ai/langgraph`

Suggested inspection targets:

- model routing implementation
- health checks and fallback behavior
- task state persistence
- tool-call validation
- permission/sandbox model
- retry and escalation logic
- structured output parsing
- local model provider adapters


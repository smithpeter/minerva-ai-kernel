# Future PC And Agent OS Architecture Watchlist

Date: 2026-06-04

## Purpose

This watchlist tracks external architecture signals that affect Minerva's
strategic direction as an agent-native bootstrap and reliability layer.

The question to keep asking:

```text
Where will the future computer enforce agent identity, capability, recovery,
and audit?
```

## Signals To Track

| Source | Signal | Why it matters to Minerva |
| --- | --- | --- |
| NVIDIA RTX Spark | Windows PCs purpose-built for personal agents, local models, large unified memory, and secure on-device agent execution. | Confirms the PC is becoming a local agent computer, not only a cloud terminal. |
| NVIDIA DGX Station for Windows | Deskside Windows AI supercomputer for developing and running always-on agents locally, with secure runtime integration. | Shows "AI PC" scales from laptops to workstation-class local agent infrastructure. |
| NVIDIA Vera | CPU designed for agentic workloads, including agent tool use and sandbox execution. | Confirms agent runtime is not only GPU inference; CPU control paths matter. |
| Microsoft Windows | Windows becoming an agent-native runtime with OS-enforced containment. | Confirms the OS layer will expose or require policy and sandbox primitives. |
| Microsoft Windows developer platform | Windows agent identity, OS-enforced containment, and enterprise manageability are becoming developer-facing platform primitives. | Confirms Minerva's ABI should map to identity, capability, policy, and audit hooks instead of only CLI commands. |
| Microsoft Foundry / Windows AI | Local model and runtime distribution across CPU/GPU/NPU. | Confirms agent capability will be heterogeneous and device-local. |
| Google Android XR / Gemini | Assistant sees user context and takes actions on behalf of the user. | Confirms mobile and XR devices will need action authorization and audit. |
| Apple Foundation Models / App Intents | On-device private intelligence with tool callbacks into apps. | Confirms local model + app action surfaces are becoming mainstream. |
| Anthropic MCP | Standardized tool/data connection layer for AI assistants. | Minerva can sit under MCP as policy, audit, and failure interpreter. |
| Google A2A | Agent-to-agent interoperability. | Minerva can provide local trust and failure semantics for agent collaboration. |
| OpenAI Agents SDK | Controlled workspaces, tools, traces, and sandbox execution. | Confirms production agents need execution boundaries and observability. |
| coreboot / UEFI | Boot payloads and firmware separation of concerns. | Provides a safe mental model for pre-OS Minerva experiments. |
| Android Verified Boot | Hardware-rooted trust chain for Android boot integrity. | Forces Android strategy to respect signed boot chains and OEM integration. |
| Agent OS research | AOS concepts map agents to scheduling, state, capability, policy, and audit responsibilities. | Gives Minerva a systems-language category beyond product positioning. |

## Primary Sources

- NVIDIA RTX Spark and Microsoft Windows PCs for personal AI:
  <https://nvidianews.nvidia.com/news/nvidia-microsoft-windows-pcs-agents-rtx-spark>
- NVIDIA Vera CPU for agents:
  <https://nvidianews.nvidia.com/news/nvidia-unveils-vera-the-cpu-for-agents>
- NVIDIA DGX Station for Windows:
  <https://nvidianews.nvidia.com/news/nvidia-dgx-station-for-windows-puts-a-trillion-parameter-ai-supercomputer-on-every-enterprise-desk>
- Microsoft Build 2026 agent-native Windows:
  <https://blogs.microsoft.com/blog/2026/06/02/microsoft-build-2026-be-yourself-at-work/>
- Windows RTX Spark platform notes:
  <https://blogs.windows.com/windowsexperience/2026/05/31/introducing-a-powerful-new-chapter-for-windows-pcs-accelerated-by-nvidia-rtx-spark/>
- Windows developer platform notes for secure local agents:
  <https://blogs.windows.com/windowsdeveloper/2026/06/02/build-2026-furthering-windows-as-the-trusted-platform-for-development/>
- Google Android XR with Gemini:
  <https://blog.google/products-and-platforms/platforms/android/android-xr-gemini-glasses-headsets/>
- Apple Foundation Models framework:
  <https://www.apple.com/newsroom/2025/09/apples-foundation-models-framework-unlocks-new-intelligent-app-experiences/>
- Anthropic Model Context Protocol:
  <https://www.anthropic.com/news/model-context-protocol?pubDate=20250519>
- Google Agent2Agent:
  <https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/>
- OpenAI Agents SDK evolution:
  <https://openai.com/index/the-next-evolution-of-the-agents-sdk/>
- coreboot documentation:
  <https://doc.coreboot.org/>
- Android Verified Boot:
  <https://source.android.google.cn/docs/security/features/verifiedboot?hl=en>
- Agent Operating Systems paper:
  <https://arxiv.org/abs/2606.01508>

## Questions For Each New Keynote Or Platform Release

1. Is the vendor moving agent execution closer to the device?
2. Is the vendor adding OS-level identity, containment, permissions, or audit?
3. Are local models becoming default, optional, or developer-managed?
4. What hardware path is emphasized: CPU, GPU, NPU, unified memory, or cloud?
5. Can third-party developers access the agent action surface?
6. Does the platform expose policy hooks or only app-level APIs?
7. Does the platform support recovery when the local model, tool, or network fails?
8. Does the platform expose logs that a tool like Minerva can interpret?
9. Are boot, recovery, installer, or device-management paths mentioned?
10. Does the platform align with MCP, A2A, or another agent protocol?

## Green Flags For Minerva

- Vendors emphasize local/private agents.
- Vendors expose sandbox and containment APIs.
- Agent tool use becomes OS-managed.
- AI PCs ship with large unified memory and local model runtimes.
- Agent protocols standardize tool and agent communication.
- Enterprises require audit and deterministic policy around agents.
- Recovery and install workflows become more complex because of local AI stacks.

## Red Flags For Minerva

- Vendors fully close the local agent runtime with no extension points.
- Agent safety is handled only at cloud API level.
- OS vendors do not expose sufficient audit or policy hooks.
- Users reject always-on local agents because of privacy concerns.
- Secure Boot / Verified Boot policies make third-party bootstrap layers
  impossible without OEM partnerships.

## Recommended Review Cadence

Monthly:

- NVIDIA blogs and GTC/Computex/CES announcements.
- Microsoft Build, Windows AI, Windows ML, Foundry Local, and Surface updates.
- Google I/O, Android, Android XR, Gemini Nano, A2A updates.
- Apple WWDC, Foundation Models, App Intents, Apple Intelligence updates.
- OpenAI, Anthropic, and agent protocol/security updates.
- coreboot, UEFI, Android Verified Boot, Linux sandboxing, and secure boot news.

Quarterly:

- Update Minerva strategy docs.
- Re-score the pre-OS feasibility path.
- Add or close research tasks.
- Check whether QEMU/bootstrap proof should advance to hardware lab work.

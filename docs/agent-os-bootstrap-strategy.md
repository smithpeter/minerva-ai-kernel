# Minerva Agent OS Bootstrap Strategy

Date: 2026-06-04

## Decision

Minerva should keep its current practical product surface as a CPU-local failure
interpreter, but open a strategic research track:

```text
Minerva as an AI bootstrap and reliability layer for agent-native computers.
```

The correct near-term goal is not to replace BIOS, UEFI, Android Verified Boot,
Windows, Linux, Android, or macOS. The correct goal is to define and prove a
portable layer that can run before, beside, and underneath normal agent
workloads:

```text
observe -> interpret -> authorize -> execute bounded action -> audit -> recover
```

This makes Minerva closer to an agent reliability kernel than an agent
framework.

## Why This Became More Important

Recent public signals indicate that personal computing is moving from
app-native interaction toward agent-native interaction:

- NVIDIA and Microsoft announced RTX Spark Windows PCs purpose-built for
  personal agents, with up to 1 petaflop of AI performance, up to 128GB unified
  memory, and new security primitives for running local agents securely.
  Source: [NVIDIA Newsroom, May 31 2026](https://nvidianews.nvidia.com/news/nvidia-microsoft-windows-pcs-agents-rtx-spark)
- NVIDIA also announced DGX Station for Windows, a deskside AI supercomputer
  for developing and running always-on agents on Windows, with NVIDIA OpenShell
  using new Windows security and containment primitives.
  Source: [NVIDIA Newsroom, May 31 2026](https://nvidianews.nvidia.com/news/nvidia-dgx-station-for-windows-puts-a-trillion-parameter-ai-supercomputer-on-every-enterprise-desk)
- NVIDIA also announced Vera as a CPU designed for agentic workloads, explicitly
  calling out agent tool use and sandbox execution as CPU-critical paths.
  Source: [NVIDIA Newsroom, May 31 2026](https://nvidianews.nvidia.com/news/nvidia-unveils-vera-the-cpu-for-agents)
- Microsoft Build 2026 described Windows as becoming an agent-native runtime,
  with operating-system-enforced containment for agent environments.
  Source: [Microsoft Blog, Jun 2 2026](https://blogs.microsoft.com/blog/2026/06/02/microsoft-build-2026-be-yourself-at-work/)
- Microsoft's Windows RTX Spark announcement says Windows is being optimized for
  agents with OS-enforced identity, containment, and manageability.
  Source: [Windows Experience Blog, May 31 2026](https://blogs.windows.com/windowsexperience/2026/05/31/introducing-a-powerful-new-chapter-for-windows-pcs-accelerated-by-nvidia-rtx-spark/)
- Microsoft's Windows developer platform notes make the same point from the
  platform side: secure local agents require OS-enforced containment, identity,
  and enterprise-grade manageability.
  Source: [Windows Developer Blog, Jun 2 2026](https://blogs.windows.com/windowsdeveloper/2026/06/02/build-2026-furthering-windows-as-the-trusted-platform-for-development/)
- Google is pushing Gemini into Android XR devices where the assistant can share
  the user's vantage point, understand what the user sees, and take actions on
  the user's behalf.
  Source: [Google Blog, I/O 2025](https://blog.google/products-and-platforms/platforms/android/android-xr-gemini-glasses-headsets/)
- Apple opened its on-device Foundation Models framework to app developers,
  emphasizing offline, private local intelligence and tool callbacks into apps.
  Source: [Apple Newsroom, Sep 29 2025](https://www.apple.com/newsroom/2025/09/apples-foundation-models-framework-unlocks-new-intelligent-app-experiences/)
- MCP and A2A show that agents are standardizing around tool access and
  agent-to-agent communication, but these protocols still need local policy,
  containment, audit, and failure recovery underneath them.
  Sources: [Anthropic MCP](https://www.anthropic.com/news/model-context-protocol?pubDate=20250519),
  [Google A2A](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- Recent systems research is already naming the category: Agent Operating
  Systems integrate agentic control planes with traditional OS responsibilities,
  especially scheduling, memory/state, tool registries, policy/trust, and audit.
  Source: [arXiv:2606.01508](https://arxiv.org/abs/2606.01508)

The strategic implication:

```text
The future PC is less "an app launcher" and more "a local agent platform".
That platform will need a lower reliability and authorization layer.
```

## Core Thesis

Traditional operating systems were designed around deterministic applications.
Agent-native computers add long-running probabilistic workers that:

- observe screens, files, logs, and services
- call tools dynamically
- operate across applications
- run locally and remotely
- need identity, containment, and audit
- fail in new ways

The missing layer is not another chatbot or agent framework. The missing layer
is a small, local, verifiable control surface:

```text
Agent intent is probabilistic.
Minerva authorization must be deterministic.
```

## "Install Before The OS" Interpretation

The founder-level idea is:

```text
Install Minerva first, then install the operating system above it.
```

This is strategically interesting, but it has several meanings. They should be
separated:

| Layer | Meaning | Feasibility | Minerva stance |
| --- | --- | --- | --- |
| Firmware payload | Minerva runs as a UEFI/coreboot payload before any OS loader. | High risk, hardware-specific. | Research only after ABI stability. |
| Bootable installer / rescue image | Minerva runs from USB, PXE, recovery, or initramfs before installing or repairing an OS. | Feasible and valuable. | Best first pre-OS product. |
| Hypervisor / sidecar | Minerva runs beside the guest OS and observes/controls bounded actions. | Feasible on x86/dev boxes. | Strong medium-term path. |
| Early userspace daemon | Minerva starts immediately after kernel boot as `minervad`. | Feasible. | Strong near-term path. |
| App/privileged service | Minerva runs inside Android/Windows/macOS with OS APIs. | Feasible but vendor-limited. | Necessary adoption bridge. |
| OEM-integrated secure service | Minerva is signed into firmware/recovery/OS image by device maker. | Strategic but partner-dependent. | Long-term target. |

Therefore the first strategic product should not be "AI BIOS". It should be:

```text
Minerva Rescue / Minerva Bootstrap Installer
```

This bootable environment runs before the user's permanent OS and can:

- inspect hardware and firmware state
- verify storage, network, and boot readiness
- install or repair an OS
- diagnose installation failures locally
- keep a signed audit trail
- install `minervad` into the target OS
- create a recovery partition or boot entry

## Why This Has Strategic Value

If Minerva is present before the main OS, it can own the first reliable
interpretation path when the machine is not yet healthy:

- OS install failed
- bootloader failed
- network install failed
- driver missing
- disk partitioning failed
- package repository unavailable
- Secure Boot / Verified Boot state unclear
- agent runtime not yet installed
- local model unavailable
- remote model unreachable

This creates a new category:

```text
AI-native installer and recovery layer
```

The user value is simple:

```text
The machine can explain why it cannot become usable yet.
```

## Architecture

```text
Hardware / Firmware
  |
  v
Bootloader / Recovery / Live Installer
  |
  v
Minerva Bootstrap Runtime
  - hardware and boot observation
  - storage and network observation
  - local CPU model or deterministic baseline
  - policy engine
  - bounded executor
  - audit log
  - OS installer bridge
  |
  v
Target OS
  - minervad early service
  - policy packs
  - taxonomy packs
  - model packs
  - adapter packs
  |
  v
Agent Frameworks / MCP / A2A / Apps
```

## Kernel ABI Direction

Minerva should define a stable Agent Kernel ABI, not only a CLI.

Candidate ABI calls:

```text
minerva.observe(event) -> observation
minerva.decide(observation, context) -> decision
minerva.authorize(decision, capabilities) -> policy_decision
minerva.execute(decision) -> observation
minerva.audit(record) -> receipt
minerva.escalate(record, target) -> escalation
```

Candidate capability classes:

```text
filesystem.read
filesystem.write
process.exec
network.dns
network.http
secrets.read
boot.inspect
boot.modify
partition.inspect
partition.modify
os.install
os.repair
agent.tool_call
agent.memory_read
agent.memory_write
```

The model should never directly own these capabilities. The model proposes a
decision. Policy grants or denies capability use. The executor maps approved
capabilities to deterministic operations.

## x86 Path

Best first path:

```text
Bootable Linux live image + Minerva runtime + OS installer bridge.
```

This avoids firmware bricking risk while still proving the "before the OS"
concept.

Milestones:

1. `minerva-bootstrap` live ISO boots in QEMU.
2. It runs `minerva doctor`, `provider-health`, and baseline decisions offline.
3. It observes storage, CPU, memory, firmware mode, network, and install media.
4. It can launch a normal Linux installer and record failures.
5. It installs `minervad` into the installed OS.
6. It creates a recovery boot entry or partition.

Later research paths:

- UEFI application that launches Minerva Rescue.
- coreboot payload experiment on supported developer hardware.
- TPM-backed audit receipts.
- Secure Boot signing and key enrollment flow.

Important reference: coreboot's own design is to perform minimal hardware
initialization and hand control to a payload. Minerva should learn from that
separation of concerns rather than trying to become full firmware.
Source: [coreboot documentation](https://doc.coreboot.org/)

## Android Path

Normal Android phones are more constrained than x86 PCs because modern devices
use a strong verified boot chain. Android Verified Boot establishes trust from a
hardware-protected root through the bootloader and verified partitions.
Source: [Android Verified Boot](https://source.android.google.cn/docs/security/features/verifiedboot?hl=en)

Therefore Minerva should not start by bypassing Android Verified Boot.

Practical Android phases:

1. Android app mode: local diagnosis of app/tool/model failures.
2. ADB developer mode: `minerva observe` for Android build, install, logcat, and
   device state.
3. Recovery image mode for unlocked developer devices.
4. AOSP system service mode for custom ROMs and dedicated devices.
5. OEM/ODM signed recovery or system service for production devices.

The Android version of the idea is:

```text
Minerva as signed recovery and agent-safety service, not a boot-chain bypass.
```

## Relationship To Existing OS Vendors

Minerva should not compete head-on with Windows, Android, macOS, or Linux.

Minerva should become the portable reliability and policy substrate that these
systems and their agent frameworks can call:

```text
Windows agent runtime -> Minerva ABI
Android/XR assistant -> Minerva ABI
Linux desktop agent -> Minerva ABI
CI runner -> Minerva ABI
MCP server -> Minerva ABI
A2A agent -> Minerva ABI
```

This is how Minerva can become lower-level without requiring immediate control
over firmware or the OS distribution channel.

## Product Lines

### 1. Minerva Kernel ABI

Stable schemas and API calls for observation, decision, authorization,
execution, audit, and escalation.

### 2. Minerva Rescue

Bootable x86 installer/recovery image for offline diagnosis and OS installation
assistance.

### 3. Minervad

Early userspace daemon that survives normal OS operation and provides the local
agent reliability surface.

### 4. Minerva Policy Packs

Capability and risk profiles for developer machines, CI runners, Android
devices, enterprise desktops, and edge nodes.

### 5. Minerva Model Packs

Small CPU/GGUF models and deterministic fallbacks optimized for failure
classification, safe action selection, and escalation.

### 6. Minerva Adapter Packs

Bridges to MCP, A2A, OpenAI Agents SDK, Windows local agent runtimes, Android
developer workflows, CI systems, and ops platforms.

## Non-Goals

Do not build these first:

- general-purpose OS
- firmware replacement
- bootloader replacement
- Android verified boot bypass
- unrestricted auto-repair
- general chatbot
- full agent framework
- GPU inference engine
- app store

## Risks

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Firmware bricking | Firmware-level work can destroy bootability. | Start with QEMU/live ISO. |
| Secure Boot complexity | Production machines require signed boot chains. | Treat signing as a later milestone. |
| Android lock-in | Many phones cannot run custom boot code. | Start with app/ADB/recovery/OEM phases. |
| Model hallucination | Pre-OS actions can be dangerous. | Deterministic policy and read-only defaults. |
| User trust | "AI below OS" sounds invasive. | Local-only, auditable, explicit capabilities. |
| Vendor conflict | OS vendors want to own agent runtime. | Position as ABI/policy/audit substrate. |
| Scope drift | OS-level ambition can swallow the current product. | Keep current M0/M1 loop as proof base. |

## Roadmap

### Track A: Current Product Proof

Continue:

- CI and agent failure interpretation
- corpus growth
- eval reporting
- CPU model benchmark
- read-only executor hardening

### Track B: Agent Kernel ABI

Deliver:

- `agent_kernel_abi.v0` document
- capability schema
- audit receipt schema
- boot/recovery observation extensions
- adapter contract for MCP/A2A/agent SDKs

### Track C: Bootstrap Installer Spike

Deliver:

- QEMU-bootable live image prototype
- offline Minerva baseline inside image
- hardware/storage/network observation
- installer failure record
- post-install `minervad` handoff design

### Track D: Rust Runtime Boundary

Deliver:

- Rust policy engine prototype
- Rust audit writer prototype
- Rust safe executor prototype
- C ABI / WASM feasibility note

### Track E: Android Feasibility

Deliver:

- Android build/logcat observation adapter
- ADB workflow
- recovery image feasibility note
- AVB-compatible OEM integration requirements

## First Strategic Task

Create a research spike:

```text
T57: Define Minerva Agent OS Bootstrap Layer v0
```

Goal:

```text
Turn Minerva from a CI-local failure interpreter into a credible agent-native
bootstrap and reliability layer without breaking the current M0/M1 product.
```

Acceptance criteria:

- Document Agent Kernel ABI v0.
- Add boot/recovery observation schema extensions.
- Define first capability taxonomy.
- Build a QEMU-only proof plan for Minerva Rescue.
- Define Android feasibility phases without bypassing Verified Boot.
- Identify which runtime pieces must move to Rust before pre-OS execution.
- Keep current CLI and CI workflows working.

## Strategic Summary

The deeper opportunity is real:

```text
Future PCs will be local agent computers.
Agent computers need a reliability, authorization, and recovery layer.
Minerva can become that layer if it moves downward carefully.
```

The first move should be:

```text
from failure interpreter -> Agent Kernel ABI -> bootable rescue installer
```

Not:

```text
from failure interpreter -> custom OS
```

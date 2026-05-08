# Policies

Policy packs define what Minerva may recommend or execute.

Default policy:

```text
read-only
no destructive commands
no credential access
no writes
```

Runtime v0 blocks:

```text
unknown action labels
dangerous action labels
shell and write-capable tools
destructive command attempts
credential path or token access attempts
```

CLI check:

```bash
minerva policy-check decision.json
```

The command prints whether the payload is allowed or blocked and includes the
policy decision reason. It does not execute the payload.

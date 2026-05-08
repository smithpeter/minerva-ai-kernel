# Pack Manifest Examples

These files are machine-readable examples for ecosystem contributions:

- `taxonomy-pack.manifest.json`
- `policy-pack.manifest.json`
- `model-pack.manifest.json`
- `adapter-pack.manifest.json`

Each manifest uses `schema_version: minerva.pack_manifest.v0` and includes:

- Required identity fields: `pack_type`, `id`, `name`, `version`,
  `description`, and `license`.
- Ownership fields: `ownership.owner`, `ownership.maintainers`,
  `ownership.reviewers`, and support notes.
- Compatibility fields: supported Minerva versions and schema versions.
- Safety fields: redaction, policy gating, no auto-repair by default,
  CPU-local minimum-path preservation, remote-service requirements, secrets
  handling, and risk notes.
- One type-specific object named after the pack type: `taxonomy`, `policy`,
  `model`, or `adapter`.

## Validation

The lightweight repository validation checks that every example manifest is
valid JSON and contains the required identity, ownership, compatibility, safety,
and type-specific fields:

```bash
python3 -m unittest tests.test_pack_manifest_examples
```

Pack maintainers should extend this with pack-specific validation before
publishing. A real pack should also validate duplicate IDs, schema names,
supported action labels, eval fixtures, policy allow/deny behavior, redaction
coverage, and unsafe-path handling.

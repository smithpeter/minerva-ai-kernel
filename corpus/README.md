# Corpus

## Real-World Corpus

`real_world_v0` contains 50 redacted GitHub Actions failure-log excerpts from
three public Python repositories:

- `pytest-dev/pytest` under the MIT license.
- `encode/httpx` under the BSD-3-Clause license.
- `fastapi/fastapi` under the MIT license.

The slice is checked in at `corpus/real_world_v0/entries.jsonl`. Each line has:

```json
{"id":"...","repo":"...","run_url":"...","raw_log_redacted":"...","expected_failure_label":"...","expected_action":"...","license_note":"..."}
```

The corpus was built with:

```bash
python3 scripts/build_real_world_corpus.py --offline
```

`scripts/build_real_world_corpus.py` has the source run URL list embedded in
`DEFAULT_SOURCES`. In a normal networked environment, omit `--offline` to let
the script ask the GitHub CLI to fetch missing public Actions logs. In this
workspace, the checked-in slice was generated from the GitHub CLI cache after
fetching the listed public runs with `gh run view --log-failed`.

The builder keeps bounded raw log excerpts, removes ANSI control codes, and
redacts emails, GitHub/user-home paths, token-like values, and long opaque hex
identifiers before writing JSONL.

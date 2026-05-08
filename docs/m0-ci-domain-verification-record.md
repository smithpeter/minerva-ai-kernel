# M0 CI And Domain Verification Record

Date: 2026-05-08.

This record captures the pre-launch verification process for GitHub Actions,
`minervakernel.com`, and launch blockers without requiring secret access. It is
intended to be copied or updated for the release commit immediately before a
public announcement.

The intended static public page artifact is
[public-site/index.html](../public-site/index.html). Use the
[minervakernel.com domain cutover runbook](minervakernel-domain-cutover-runbook.md)
for nginx/static-host setup, certificate requirements, rollback, and readiness
verification commands.

Preferred repeatable command:

```bash
python3 scripts/check-release-readiness.py --content-reviewed "Verified public Minerva page"
```

The script checks the local commit, attempts to read GitHub Actions status for
that commit through an existing `gh` session, and checks DNS, TLS, and HTTPS
reachability for `minervakernel.com`. It also probes the local
`setuptools.build_meta` build backend needed by the documented offline editable
install path. The HTTPS check requires Minerva brand/content signals in the
public page title or body and rejects VoxSign markers in redirects or page
content. It does not mutate DNS, deploy a site, create credentials, print
environment dumps, print response bodies, bypass TLS, or download dependencies.

## Current Domain Blocker: VoxSign Contamination

On 2026-05-08, readiness for commit
`109b524467b6fb6cf78f00c86416b070c4691226` was a no-go even though CI was green
and DNS resolved. Direct TLS diagnostics showed `minervakernel.com` presenting a
certificate with subject `CN=test.voxsign.net`, which is not valid for
`minervakernel.com`. Fetching only after disabling certificate verification
returned a VoxSign page title and VoxSign content.

Required external fix: `minervakernel.com` must serve a certificate valid for
`minervakernel.com` and the intended Minerva page artifact, not a VoxSign
certificate, VoxSign preview, parking page, stale preview, or unrelated
service. Do not use `curl -k`, `--insecure`, or any certificate-verification
bypass as passing readiness evidence.

Recheck the domain blocker with:

```bash
python3 scripts/check-release-readiness.py --skip-github-actions --content-reviewed "Verified public Minerva page"
```

## Verified Facts From Local Checkout

These facts can be verified from a clean local checkout without external
credentials.

| Fact | Verification Command | Expected Result |
| --- | --- | --- |
| Repository root is the Minerva checkout. | `git rev-parse --show-toplevel` | Path ends in `minerva-ai-kernel`. |
| Release commit is known. | `git rev-parse HEAD` | Record the full commit SHA. |
| Local compile gate passes. | `python3 -m compileall minerva_kernel` | Command exits 0. |
| Local unit gate passes. | `python3 -m unittest discover -s tests` | Command exits 0 and reports `OK`. |
| Local eval smoke gate is available for release readiness. | `python3 -m minerva_kernel.eval_smoke` | Command exits 0 and reports all smoke cases passed. |
| Public static artifact is present and clean. | `python3 -m unittest tests.test_public_site_artifact` | Command exits 0 and verifies required Minerva signals, docs/GitHub links, and no rejected markers in `public-site/`. |
| Repeatable readiness checker is available. | `python3 scripts/check-release-readiness.py --skip-external` | Local checkout metadata and current-interpreter install-backend status are reported; external checks are marked `skipped`. |
| Fresh venv has the offline editable-install backend. | `python3 scripts/check-release-readiness.py --skip-external --install-backend fresh-venv` | `local_install_backend` is `pass`, or a setup blocker is recorded before the install dry run. |
| Public docs can be searched for launch blockers. | `rg -n "auto[- ]?repair|replace CI|full AIOps|credential|secret|API key" README.md docs examples` | Any match is reviewed in context before announcement. |

Local verification is necessary but not sufficient for release. The release
owner must also confirm remote CI, DNS, TLS, and final target content.

## Release-Owner Manual Confirmations

These checks may require repository or domain ownership context, but they must
not require adding secrets to this checkout.

| Area | Required Confirmation | Evidence To Record |
| --- | --- | --- |
| GitHub Actions status | The GitHub Actions compile/test/eval smoke gate is green on the exact release branch or announcement commit. | Workflow run URL, commit SHA, branch, conclusion, and timestamp. |
| Domain DNS target | `minervakernel.com` resolves to the intended public project surface or announcement destination. | DNS provider target, observed A/AAAA/CNAME records, and timestamp. |
| Domain TLS | `https://minervakernel.com/` presents a valid certificate for `minervakernel.com`. | Certificate subject/SAN, issuer, validity window, and timestamp. |
| Domain content | The loaded HTTPS page is the intended public Minerva page from `public-site/index.html` or an approved successor, not a VoxSign page, parking page, stale preview, or unrelated service. | URL, page title or landing identifier, screenshot or reviewer note, and timestamp. |
| Launch blockers | No release-readiness launch blocker is open. | Checklist reviewer, reviewed commit, and explicit go/no-go decision. |

## No-Secret Commands

The commands below are safe to run locally. They do not modify DNS, deploy a
site, create external accounts, or require secret values.

Repeatable readiness checker:

```bash
python3 scripts/check-release-readiness.py --content-reviewed "Verified public Minerva page"
```

Local-only dry run, useful when network or repository access is unavailable:

```bash
python3 scripts/check-release-readiness.py --skip-external --install-backend auto
```

Fresh-venv install-backend dry run:

```bash
python3 scripts/check-release-readiness.py --skip-external --install-backend fresh-venv
```

The checker output is bounded for public issue comments. It reports statuses as
`pass`, `fail`, `unverified`, `manual`, or `skipped`; omits local full paths,
tokens, response bodies, and environment dumps; and exits non-zero when an
automated check fails, an external check is unverified, or HTTPS content review
has not been recorded. Use `--content-reviewed` only after the release owner has
opened the HTTPS page and confirmed that it is the intended public Minerva
surface. The note does not override TLS validation or the automated Minerva
brand guard.

What the checker verifies locally:

- Repository root basename, current commit SHA, current branch, and repository
  slug.
- Whether `setuptools.build_meta` is importable in a bounded set of discovered
  local Python candidates, in one selected target interpreter, or in a fresh
  venv when `--install-backend fresh-venv` is used.
- Whether the repeatable process can run without external access by using
  `--skip-external`.

Interpret `local_install_backend` as follows:

- `pass`: the selected or discovered local target has the build backend needed for
  `python -m pip install --no-index --no-deps --no-build-isolation -e .`.
- `fail`: use a local interpreter or venv that already provides
  `setuptools.build_meta`, or seed it from an approved local wheel/cache before
  rerunning; do not download dependencies during this readiness check.
- `skipped`: the install-backend check was intentionally omitted and separate
  evidence is required before relying on the offline editable install path.

What requires external permissions or network availability:

- GitHub Actions status for the current commit requires network access, the
  `gh` CLI, and either public API access or an already authenticated session.
- DNS readiness requires public resolver availability.
- TLS readiness requires network access and public CA trust.
- HTTPS readiness requires the public endpoint to respond.
- HTTPS brand readiness requires Minerva title/body signals and no VoxSign
  markers in redirects or content.
- Final HTTPS content correctness still requires release-owner human review.

Local release gates:

```bash
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
python3 -m minerva_kernel.eval_smoke
python3 -m unittest tests.test_public_site_artifact
```

GitHub Actions status, when the release owner already has access through the
GitHub UI or an existing `gh` session:

```bash
python3 scripts/check-release-readiness.py --skip-domain
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
gh run list --repo smithpeter/minerva-ai-kernel --branch "$(git rev-parse --abbrev-ref HEAD)" --limit 10
```

If `gh` is unavailable or unauthenticated, record the same facts from the
repository's GitHub Actions web page. Do not create or paste tokens just to fill
this record.

Domain DNS, TLS, and brand checks:

```bash
python3 scripts/check-release-readiness.py --skip-github-actions --content-reviewed "Verified public Minerva page"
dig +short A minervakernel.com
dig +short AAAA minervakernel.com
dig +short CNAME minervakernel.com
dig +short NS minervakernel.com
curl -I --proto =https --tlsv1.2 https://minervakernel.com/
openssl s_client -servername minervakernel.com -connect minervakernel.com:443 </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
```

The `dig`, `curl`, and `openssl` commands report observed DNS and TLS state
only. They do not prove that the content is correct; the release owner must
inspect the final HTTPS page. The readiness script is the required automated
guard for the Minerva/VoxSign brand check.

## Example Release Record

Use this shape for the announcement commit.

```text
Release commit:
Release branch:
Verification timestamp:

Verified locally:
- compileall:
- unittest:
- eval_smoke:
- launch-blocker doc search:

Manual confirmations:
- GitHub Actions run URL:
- GitHub Actions conclusion:
- minervakernel.com DNS target:
- minervakernel.com TLS certificate:
- minervakernel.com HTTPS content:
- Public artifact/runbook reviewed:
- Release owner go/no-go:
```

## Launch Blocker Review

No-go if any of the following are true:

- Local compile, unit tests, eval smoke, or remote CI fails on the release
  commit.
- GitHub Actions status is missing, red, cancelled, or for a different commit.
- `minervakernel.com` does not resolve to the intended public target.
- HTTPS for `minervakernel.com` is unavailable, expired, mismatched, or points
  to VoxSign or other unrelated content.
- Public docs imply Minerva M0 auto-repairs systems, replaces CI or monitoring,
  requires a remote LLM for the minimum path, or is a full AIOps platform.
- Public docs, examples, fixtures, or release materials expose secrets,
  credentials, private logs, full environment dumps, or proprietary data.

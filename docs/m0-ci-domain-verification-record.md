# M0 CI And Domain Verification Record

Date: 2026-05-08.

This record captures the pre-launch verification process for GitHub Actions,
`minervakernel.com`, and launch blockers without requiring secret access. It is
intended to be copied or updated for the release commit immediately before a
public announcement.

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
| Domain content | The loaded HTTPS page is the intended public Minerva page, not a parking page, stale preview, or unrelated service. | URL, page title or landing identifier, screenshot or reviewer note, and timestamp. |
| Launch blockers | No release-readiness launch blocker is open. | Checklist reviewer, reviewed commit, and explicit go/no-go decision. |

## No-Secret Commands

The commands below are safe to run locally. They do not modify DNS, deploy a
site, create external accounts, or require secret values.

Local release gates:

```bash
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
python3 -m minerva_kernel.eval_smoke
```

GitHub Actions status, when the release owner already has access through the
GitHub UI or an existing `gh` session:

```bash
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
gh run list --repo smithpeter/minerva-ai-kernel --branch "$(git rev-parse --abbrev-ref HEAD)" --limit 10
```

If `gh` is unavailable or unauthenticated, record the same facts from the
repository's GitHub Actions web page. Do not create or paste tokens just to fill
this record.

Domain DNS and TLS checks:

```bash
dig +short A minervakernel.com
dig +short AAAA minervakernel.com
dig +short CNAME minervakernel.com
dig +short NS minervakernel.com
curl -I --proto =https --tlsv1.2 https://minervakernel.com/
openssl s_client -servername minervakernel.com -connect minervakernel.com:443 </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates
```

These commands report observed DNS and TLS state only. They do not prove that
the content is correct; the release owner must inspect the final HTTPS page.

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
- Release owner go/no-go:
```

## Launch Blocker Review

No-go if any of the following are true:

- Local compile, unit tests, eval smoke, or remote CI fails on the release
  commit.
- GitHub Actions status is missing, red, cancelled, or for a different commit.
- `minervakernel.com` does not resolve to the intended public target.
- HTTPS for `minervakernel.com` is unavailable, expired, mismatched, or points
  to unrelated content.
- Public docs imply Minerva M0 auto-repairs systems, replaces CI or monitoring,
  requires a remote LLM for the minimum path, or is a full AIOps platform.
- Public docs, examples, fixtures, or release materials expose secrets,
  credentials, private logs, full environment dumps, or proprietary data.

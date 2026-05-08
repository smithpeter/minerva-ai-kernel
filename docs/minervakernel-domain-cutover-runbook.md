# Minerva Domain Cutover Runbook

This runbook moves `minervakernel.com` to the standalone Minerva public page
artifact without changing application code or deploying from this repository.
It is an operator checklist for the release owner.

## Scope

Use this artifact as the web root:

```text
public-site/index.html
```

The page is static HTML with inline CSS and no runtime build step. It can be
served by nginx, a CDN-backed static host, an object store static website, or a
managed static-site platform.

Do not claim the domain is fixed until the verification section passes with
valid TLS and intended Minerva content.

## Preflight

From the repository root:

```bash
git rev-parse --show-toplevel
test -f public-site/index.html
python3 -m unittest tests.test_public_site_artifact
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
```

The first command must point at the Minerva checkout. The public artifact test
must pass before uploading or publishing the artifact.

Check that the artifact does not contain rejected brand markers:

```bash
if rg -ni "voxsign|test\\.voxsign\\.net" public-site; then
  echo "public artifact contains rejected brand markers" >&2
  exit 1
fi
```

Confirm these inputs before touching DNS or hosting settings:

- Domain owner has access to DNS for `minervakernel.com`.
- Hosting owner has access to the nginx host or static host.
- Certificate issuer can issue for `minervakernel.com`; include
  `www.minervakernel.com` only if it will be served or redirected.
- A previous known-good Minerva artifact or maintenance page is available for
  rollback.
- Any cache layer or CDN can be purged after the cutover.

## Nginx Static Host Path

1. Stage the artifact as a static web root on the target host:

```bash
sudo install -d -m 0755 /var/www/minervakernel.com
sudo install -m 0644 public-site/index.html /var/www/minervakernel.com/index.html
```

2. Configure nginx for HTTP challenge handling and HTTPS serving. Adjust the
   certificate paths if a different issuer or automation manages them:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name minervakernel.com www.minervakernel.com;

    location /.well-known/acme-challenge/ {
        root /var/www/minervakernel.com;
    }

    location / {
        return 301 https://minervakernel.com$request_uri;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name minervakernel.com;

    root /var/www/minervakernel.com;
    index index.html;

    ssl_certificate /etc/letsencrypt/live/minervakernel.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/minervakernel.com/privkey.pem;

    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy no-referrer-when-downgrade always;

    location / {
        try_files $uri $uri/ /index.html;
    }
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name www.minervakernel.com;

    ssl_certificate /etc/letsencrypt/live/minervakernel.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/minervakernel.com/privkey.pem;

    return 301 https://minervakernel.com$request_uri;
}
```

3. Validate and reload nginx:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

4. Issue or renew the certificate after DNS points at the nginx host. With
   Certbot/nginx automation, use:

```bash
sudo certbot --nginx -d minervakernel.com -d www.minervakernel.com
```

Only include `www.minervakernel.com` when DNS and nginx are configured for it.

## Managed Static Host Path

For a managed static host, object store, or CDN-backed site:

1. Create a static site whose publish root is `public-site/`.
2. Ensure `index.html` is served for `/`.
3. Add `minervakernel.com` as the custom domain. Add `www.minervakernel.com`
   only if it will redirect or serve intentionally.
4. Enable HTTPS with a managed certificate whose SAN includes every hostname
   being served.
5. Remove stale preview aliases, unrelated project aliases, or fallback origins
   from the custom-domain configuration.
6. Update DNS records exactly as the host provider requires.
7. Purge CDN or static-host caches after publishing.

## GitHub Pages Workflow Path

The repository includes a GitHub Pages workflow:

```text
.github/workflows/pages.yml
```

The workflow runs on `main` changes that touch the public-site artifact or on
manual dispatch. It validates the static artifact tests, uploads `public-site/`
with `actions/upload-pages-artifact`, and deploys the artifact with
`actions/deploy-pages`. It does not use private server credentials or deploy to
`49.51.134.101`.

The custom-domain artifact is:

```text
public-site/CNAME
```

It contains:

```text
minervakernel.com
```

Before relying on the GitHub Pages custom domain, the release owner must:

1. Set the repository Pages source to GitHub Actions if it is not already set.
2. Confirm the `github-pages` environment and Pages deployment run are green for
   the intended commit.
3. Add or verify `minervakernel.com` in the repository's Pages custom-domain
   settings if GitHub requires an explicit settings-side confirmation.
4. Configure DNS records exactly as GitHub Pages requires for the apex domain.
5. Wait for GitHub's managed certificate to issue and become active.
6. Run the readiness verification commands below without bypassing TLS.

A successful Pages workflow is not enough to claim domain readiness. DNS,
custom-domain ownership, certificate identity, HTTPS content, and the
Minerva/VoxSign brand guard must still pass for `minervakernel.com`.

## Certificate Requirements

The certificate used for `https://minervakernel.com/` must satisfy all of the
following:

- The certificate is issued by a public CA trusted by current browsers.
- The SAN includes `minervakernel.com`.
- The SAN includes `www.minervakernel.com` if that hostname is served or
  redirected over HTTPS.
- The certificate is current, not expired, and not before its validity window.
- The certificate presented through SNI for `minervakernel.com` is the Minerva
  certificate.
- The certificate is not a preview, staging, unrelated-service, or old-project
  certificate.

Do not use `curl -k`, `--insecure`, browser warning bypasses, or any
certificate-verification bypass as passing evidence.

## DNS Cutover

1. Lower DNS TTL ahead of the cutover when possible.
2. Point `minervakernel.com` at the selected nginx/static-host target using the
   host's required A, AAAA, ALIAS, ANAME, or CNAME records.
3. Configure `www.minervakernel.com` only if the certificate and host route are
   ready for it.
4. Remove stale records that point at unrelated services or old previews.
5. Wait for propagation, then verify public resolvers from a network outside
   the hosting provider.

## Readiness Verification

Run the required local gates from the repository root:

```bash
python3 -m compileall minerva_kernel
python3 -m unittest discover -s tests
```

Verify DNS:

```bash
dig +short A minervakernel.com
dig +short AAAA minervakernel.com
dig +short CNAME minervakernel.com
dig +short NS minervakernel.com
```

Verify HTTPS and certificate identity without bypassing TLS:

```bash
curl -I --proto =https --tlsv1.2 https://minervakernel.com/
openssl s_client -servername minervakernel.com -connect minervakernel.com:443 </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates -ext subjectAltName
```

Verify the served page has Minerva content and no rejected markers:

```bash
curl -fsSL --proto =https --tlsv1.2 https://minervakernel.com/ | head -n 40
python3 scripts/check-release-readiness.py --skip-github-actions --content-reviewed "Verified public Minerva page"
```

The readiness checker must report passing DNS, TLS, HTTPS reachability, Minerva
brand signals, and no rejected markers. The `--content-reviewed` note records
human review; it does not override TLS validation or the automated brand guard.

Record the final evidence in
[M0 CI and domain verification record](m0-ci-domain-verification-record.md):

- release commit SHA
- DNS target and timestamp
- certificate subject, SAN, issuer, and validity window
- HTTPS status and final URL
- readiness checker output summary
- release-owner go/no-go decision

## Rollback

Prefer rollback to a previous known-good Minerva page or a minimal Minerva
maintenance page that still has a valid certificate for `minervakernel.com`.

Nginx rollback options:

- Restore the previous `/var/www/minervakernel.com/index.html`.
- Switch the web root symlink back to the previous Minerva release directory.
- Revert the nginx server block to the previous Minerva target and reload nginx.

Managed static-host rollback options:

- Revert to the previous published static deployment.
- Restore the previous custom-domain mapping.
- Purge CDN/static-host caches after rollback.

DNS rollback is slower and should be used only when the host target is wrong or
unrecoverable. If rollback points at unrelated content, the release remains
no-go even if DNS and TLS are reachable.

After rollback, rerun:

```bash
curl -I --proto =https --tlsv1.2 https://minervakernel.com/
python3 scripts/check-release-readiness.py --skip-github-actions --content-reviewed "Verified public Minerva page"
```

## No-Go Conditions

Do not announce or mark the domain ready when any of these are true:

- DNS resolves to an unintended host or stale preview.
- TLS is missing, expired, mismatched, or requires a verification bypass.
- HTTPS content is not the Minerva public artifact or approved Minerva
  maintenance page.
- The page weakens M0 non-claims or implies auto-repair, a full AIOps platform,
  CI replacement, or arbitrary model-generated command execution.
- The public artifact test or release readiness checker fails.

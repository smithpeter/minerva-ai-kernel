# Security

Minerva is read-only by default.

Default restrictions:

- no destructive commands
- no credential access
- no filesystem writes unless explicitly enabled
- no production repair without approval
- redaction before model input

Never collect by default:

- API keys
- tokens
- passwords
- private keys
- cloud credentials
- SSH keys
- cookies
- full `.env` files

Report security issues privately to `security@minervakernel.com` until a public
disclosure process is established.

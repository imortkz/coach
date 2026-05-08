# M004: SSL/HTTPS with Let's Encrypt — Context

**Gathered:** 2026-03-14
**Status:** Queued — pending auto-mode execution.

## Project Description

GymCoach runs on a VPS via Docker Compose (nginx + FastAPI + MongoDB). Currently HTTP-only on port 80. Telegram Login Widget requires HTTPS on a registered domain — the production auth flow is blocked without it.

## Why This Milestone

SSL was explicitly deferred in M001 pending domain purchase. It is now a hard blocker for production use: the Telegram Login Widget rejects HTTP origins, and BotFather's `/setdomain` requires HTTPS. Without this milestone, authentication cannot work in production.

## User-Visible Outcome

### When this milestone is complete, the user can:

- Access the app at `https://<domain>` with a valid TLS certificate (no browser warnings)
- Log in via Telegram Login Widget (which previously failed on plain HTTP)
- HTTP requests to port 80 redirect automatically to HTTPS
- Let's Encrypt certificates renew automatically without manual intervention

### Entry point / environment

- Entry point: `https://<domain>` — production VPS
- Environment: production-like (Docker Compose, real domain with DNS pointing to VPS IP)
- Live dependencies involved: Let's Encrypt ACME servers (HTTP-01 challenge over port 80), Telegram (validates HTTPS domain for Login Widget)

## Completion Class

- Contract complete means: `docker compose -f docker-compose.prod.yml up -d` starts stack with HTTPS; `curl -I https://<domain>/api/health` returns 200; `curl -I http://<domain>` returns 301 redirect to HTTPS
- Integration complete means: Telegram Login Widget loads and authenticates successfully at the HTTPS domain; cert is issued by Let's Encrypt (not self-signed)
- Operational complete means: certbot autorenew fires on a cron schedule and successfully renews a near-expiry cert (verified via `certbot renew --dry-run`)

## Final Integrated Acceptance

To call this milestone complete, we must prove:

- `https://<domain>` loads the SPA with a valid Let's Encrypt cert (green padlock, no mixed content warnings)
- `http://<domain>` returns HTTP 301 → `https://<domain>`
- `https://<domain>/api/health` returns `{"status":"ok","database":"connected"}`
- Telegram Login Widget completes a login flow and returns a valid JWT
- `certbot renew --dry-run` inside the certbot container exits 0
- Cron (or `crond` inside the certbot container) is confirmed running and will re-run renewal on schedule

## Risks and Unknowns

- **DNS propagation** — Domain must resolve to the VPS IP before the ACME HTTP-01 challenge fires. If DNS hasn't propagated, cert issuance fails (Let's Encrypt rate-limits retries). The plan must include a DNS verification step before running certbot.
- **Let's Encrypt rate limits** — 5 failed cert requests per domain per hour. Testing must use `--staging` flag first to avoid hitting production rate limits.
- **Port 80 bootstrap problem** — nginx must serve the ACME challenge on port 80 before certs exist, but nginx's HTTPS config references cert files that don't exist yet on first run. The plan must handle the chicken-and-egg: either a two-phase nginx config (HTTP-only first, then HTTPS after certs are issued), or a certbot webroot strategy where nginx serves `.well-known/acme-challenge/` over HTTP before 443 is configured.
- **Cert renewal and nginx reload** — After renewal, nginx must reload to pick up the new cert. This typically requires a `post-hook` in certbot's renewal config or a cron job that signals the nginx container (`docker exec nginx nginx -s reload`).
- **docker-compose.prod.yml changes** — Port 443 must be exposed on the nginx service; the certbot volume must be mounted in both the certbot and nginx containers. Changes to the production compose file require careful review — dev compose must remain unchanged.

## Existing Codebase / Prior Art

- `../nginx/nginx.conf` — Current config: `listen 80; server_name _;` — needs to gain a 443 server block with SSL cert paths and an HTTP→HTTPS redirect block; ACME challenge location must be handled
- `../nginx/Dockerfile` — Multi-stage build: node builds Vue SPA, nginx:1.28-alpine serves it; no changes needed to the build itself, but the nginx.conf template may need to become a runtime-configurable file (or a second conf file for HTTPS)
- `../docker-compose.prod.yml` — Currently exposes only port 80; needs port 443, a certbot service, and a shared certs volume
- `../DEPLOYMENT.md` — Has a placeholder "SSL setup" section that deferred this work; needs full step-by-step instructions for the certbot flow
- `../.env.example` — May need `DOMAIN` variable so nginx.conf and certbot can reference the domain name dynamically

> See `.gsd/DECISIONS.md` for all architectural and pattern decisions — it is an append-only register; read it during planning, append to it during execution.

## Relevant Requirements

No existing requirements map directly. This milestone unblocks production auth (AUTH-01 through AUTH-06 are validated in dev but not live-tested in production due to missing HTTPS).

## Scope

### In Scope

- Add `certbot/certbot` as a Docker Compose service in `docker-compose.prod.yml`
- Shared Docker volume for Let's Encrypt certs (mounted in both certbot and nginx containers)
- nginx config update: HTTP-01 ACME challenge location on port 80, HTTPS server block on port 443, HTTP→HTTPS redirect
- Bootstrap procedure: HTTP-only nginx phase → certbot certonly → nginx reload with HTTPS config
- Certbot autorenew via `crond` inside the certbot container (or `--deploy-hook` to reload nginx after renewal)
- DEPLOYMENT.md update: full SSL setup steps, staging vs production cert flag, renewal verification
- `.env.example` update: add `DOMAIN` variable
- `docker-compose.prod.yml`: expose port 443, add certbot service with webroot volume
- Dev compose (`docker-compose.yml`) remains HTTP-only — no changes

### Out of Scope / Non-Goals

- CI/CD pipeline for automated deployment
- Self-signed certs or custom CA — Let's Encrypt only
- Wildcard certificates (requires DNS-01 challenge, more complex) — single-domain cert is sufficient
- HTTP/2 or HSTS preloading — basic HTTPS is the goal
- Multiple domains or subdomains
- Changing the Caddy or Traefik — nginx stays

## Technical Constraints

- Must not break dev compose (`docker-compose.yml` stays HTTP-only, unchanged)
- nginx config must handle the ACME challenge over HTTP before certs exist (bootstrap ordering problem)
- Must use `--staging` Let's Encrypt endpoint for all testing to avoid rate limits; switch to production only for final cert issuance
- Certbot image: `certbot/certbot` (official Docker image)
- Cert storage: named Docker volume mounted at `/etc/letsencrypt` in certbot container and at a read path in nginx container
- Domain must be a real registered domain with DNS A record pointing to VPS — no bare IP support

## Integration Points

- `docker-compose.prod.yml` → certbot service + nginx service — shared volume for cert files; certbot webroot served by nginx
- `nginx/nginx.conf` → Let's Encrypt webroot path (`.well-known/acme-challenge/`) must be served over HTTP before HTTPS is configured
- Certbot post-renewal hook → `nginx -s reload` in the nginx container — certs must be picked up without a full container restart
- `DEPLOYMENT.md` → operator runbook — the bootstrap sequence (DNS → staging cert → production cert → verify renewal) must be documented clearly enough to execute without guesswork

## Open Questions

- None — design questions resolved during discussion.

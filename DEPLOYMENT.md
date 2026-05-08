# GymCoach — Deployment Guide

## Prerequisites

### 1. Docker and Docker Compose

Install Docker Engine (includes Compose v2) on your VPS:

```bash
curl -fsSL https://get.docker.com | sh
```

Verify:

```bash
docker --version          # Docker 24+
docker compose version    # Docker Compose v2+
```

### 2. Telegram Bot Setup (required for production auth)

Production mode uses the [Telegram Login Widget](https://core.telegram.org/widgets/login)
for authentication. You need a Telegram bot as an identity provider.

**Step 1 — Create a bot:**

1. Open Telegram, search for `@BotFather`
2. Send `/newbot`
3. Follow the prompts to choose a name and username
4. Copy the **bot token** (format: `123456789:AAF...`) — this is your `TELEGRAM_BOT_TOKEN`
5. Note the bot username (e.g. `MyGymCoachBot`) — this is your `VITE_TELEGRAM_BOT_NAME`

**Step 2 — Register your domain with the bot:**

The Telegram Login Widget requires a registered domain name **and HTTPS**. Bare IP addresses and `localhost` are not accepted by BotFather or the widget.

1. Get a domain name (e.g. `gymcoach.example.com`) — even a cheap one works
2. Point it at your VPS IP (DNS A record)
3. Set up HTTPS — see [SSL setup](#ssl-https-setup) below
4. Send `/setdomain` to `@BotFather`
5. Select your bot
6. Enter your domain (e.g. `gymcoach.example.com`)

> **Note:** BotFather requires a proper domain name. Bare IP addresses, `localhost`,
> and local hostnames are rejected with "The message should contain one domain name."

---

## Local Development (DEV_MODE)

For local development, Telegram auth is bypassed. No bot or domain setup required.

```bash
cd /path/to/parent/directory   # where backend/, frontend/, gsd/ live
docker compose up --build
```

The app will be accessible at `http://localhost`. Dev mode auto-logs in without credentials.

MongoDB is also exposed on port `27017` for use with Compass or mongosh:

```bash
mongosh mongodb://localhost:27017/gymcoach
```

---

## Production Deployment (VPS + Domain)

### Step 1 — Clone and configure

```bash
# On your VPS
git clone <your-repo-url>
cd <parent-directory>

# Create your .env from the example
cp .env.example .env
nano .env    # fill in JWT_SECRET, TELEGRAM_BOT_TOKEN, VITE_TELEGRAM_BOT_NAME
```

Required values in `.env`:

| Variable | How to get it |
|----------|--------------|
| `JWT_SECRET` | Run: `python3 -c "import secrets; print(secrets.token_hex(32))"` |
| `TELEGRAM_BOT_TOKEN` | From @BotFather `/newbot` |
| `VITE_TELEGRAM_BOT_NAME` | Bot username without `@` |
| `DOMAIN` | Your domain, e.g. `coach.example.com` (DNS A-record must point at the VPS public IP) |
| `ACME_EMAIL` | Your email — Let's Encrypt sends renewal failure notices here |

### Step 2 — Build and start (HTTP-only bootstrap)

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

This will:
1. Build the FastAPI backend image
2. Build the nginx image (which compiles the Vue SPA with your bot name baked in and copies the runtime templates + entrypoint)
3. Start MongoDB with a named volume for data persistence
4. Start the backend (waits for MongoDB health check)
5. Start nginx on port 80 + 443 — **in HTTP-only bootstrap mode**, because no SSL cert exists yet
6. Start certbot in renewal-loop mode (idle until first cert is issued)

First-run: the backend automatically seeds ~150 exercises into the database on startup.

The site is reachable at `http://${DOMAIN}` over plain HTTP. Telegram auth will not work yet — Telegram requires HTTPS. Issue a Let's Encrypt cert next.

### Step 3 — SSL/HTTPS Setup with Let's Encrypt

This is the cert-bootstrap flow. Run it once on first deploy. Renewals after that happen
automatically every 12h via the `certbot` service in the compose stack.

> **Anchor:** `ssl-https-setup` — referenced from the Telegram bot setup section above.

#### 3.1 — Verify DNS resolves to this VPS

ACME's HTTP-01 challenge requires Let's Encrypt to reach `http://${DOMAIN}/.well-known/acme-challenge/...` on **your** VPS. Confirm DNS first:

```bash
dig +short "${DOMAIN}"
# Expected: the public IP of this VPS. If it differs, fix the DNS A-record and wait
# 5–30 minutes for propagation before continuing.
```

#### 3.2 — Sanity-check the ACME challenge surface

While nginx is in HTTP-only bootstrap mode, the `/.well-known/acme-challenge/` location is already wired and served from the `certbot_www` volume. Quick check:

```bash
curl -I "http://${DOMAIN}/.well-known/acme-challenge/test"
# Expected: HTTP/1.1 404 Not Found  (location resolves; file just doesn't exist yet)
```

If you get a 5xx or connection refused, fix that before issuing certs — staging or prod, you'll just burn the rate-limit otherwise.

#### 3.3 — Issue a STAGING cert first

Let's Encrypt rate-limits production cert issuance to 5 failures per domain per hour. Always validate the pipeline against staging first:

```bash
docker compose -f docker-compose.prod.yml run --rm certbot \
  certonly \
  --webroot -w /var/www/certbot \
  --staging \
  -d "${DOMAIN}" \
  --email "${ACME_EMAIL}" \
  --agree-tos --no-eff-email \
  --non-interactive
```

A staging cert will be issued (untrusted by browsers but proves the flow works). If you see "Successfully received certificate" — proceed.

If it fails — read the error, fix DNS / nginx / firewall, and re-run staging until it succeeds.

#### 3.4 — Delete the staging cert and request a production cert

```bash
# Drop the staging cert so the prod issuance writes cleanly to the same path:
docker compose -f docker-compose.prod.yml run --rm certbot \
  delete --cert-name "${DOMAIN}" --non-interactive

# Issue the real cert:
docker compose -f docker-compose.prod.yml run --rm certbot \
  certonly \
  --webroot -w /var/www/certbot \
  -d "${DOMAIN}" \
  --email "${ACME_EMAIL}" \
  --agree-tos --no-eff-email \
  --non-interactive
```

#### 3.5 — Reload nginx so it picks up the new cert

The nginx entrypoint chooses HTTP-only or HTTPS template based on cert presence at startup, so a simple restart is enough:

```bash
docker compose -f docker-compose.prod.yml restart nginx
```

Logs should show: `[nginx-entrypoint] SSL cert found at /etc/letsencrypt/live/<DOMAIN>/fullchain.pem — serving HTTPS for DOMAIN=<DOMAIN>`.

#### 3.6 — Register the domain with @BotFather

Telegram's Login Widget only loads on a domain that's registered with the bot:

1. In Telegram, talk to `@BotFather`
2. `/setdomain` → pick your bot → enter `${DOMAIN}` (no `https://` prefix)

#### 3.7 — Verify renewal works without actually renewing

```bash
docker compose -f docker-compose.prod.yml run --rm certbot \
  renew --dry-run
# Exit code 0 + "all renewals succeeded" — you're set.
```

The `certbot` service in the running stack already runs `certbot renew` on a 12-hour loop; on actual renewal it touches `/var/www/certbot/.cert-renewed`, and nginx watches for that marker and reloads itself within 5 minutes.

### Step 4 — Verify the live stack

```bash
# All containers running:
docker compose -f docker-compose.prod.yml ps

# Backend health through HTTPS:
curl -I "https://${DOMAIN}/api/health"
# Expected: HTTP/2 200

# HTTP→HTTPS redirect in place:
curl -I "http://${DOMAIN}"
# Expected: HTTP/1.1 301 Moved Permanently  Location: https://${DOMAIN}/

# Logs:
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml logs nginx
docker compose -f docker-compose.prod.yml logs certbot
```

Open `https://${DOMAIN}` in a browser — you should see the GymCoach login page with a valid TLS padlock.

### Step 5 — Login

Click "Log in with Telegram" on the login page. The Telegram popup will open. After
authentication, you'll be redirected to the app with a 1-year JWT session.

---

## Data Persistence

MongoDB data is stored in a named Docker volume (`mongodb_data`). It survives:

- `docker compose restart`
- `docker compose stop && docker compose start`
- Server reboots

Data is **lost** only if you explicitly remove the volume:

```bash
# WARNING: destroys all gym data
docker compose -f docker-compose.prod.yml down -v
```

### Manual backup

```bash
# Dump to local file
docker exec gymcoach_mongodb_1 mongodump --db gymcoach --archive | gzip > gymcoach_backup_$(date +%Y%m%d).gz

# Restore
gunzip -c gymcoach_backup_20260101.gz | docker exec -i gymcoach_mongodb_1 mongorestore --archive --db gymcoach
```

---

## Updates

To update the app to a new version:

```bash
git pull
docker compose -f docker-compose.prod.yml up --build -d
```

Docker will rebuild changed images and restart only affected containers.
MongoDB data is preserved in the named volume.

---

## Troubleshooting

### Telegram widget doesn't appear / "Bot domain invalid"

- Confirm `VITE_TELEGRAM_BOT_NAME` is set correctly in `.env` (no `@` prefix)
- Confirm you ran `/setdomain` in @BotFather with the **exact domain** your site is served from
- The widget requires **HTTPS** — it will not work over plain HTTP
- Bare IP addresses and `localhost` are not valid bot domains
- Check nginx logs: `docker compose logs nginx`

### "Invalid token" after server restart

- `JWT_SECRET` in `.env` must be a stable value. If it was left blank, a random
  secret was generated at startup, invalidating previous tokens.
- Fix: set a permanent `JWT_SECRET` and restart: `docker compose restart backend`

### Backend can't connect to MongoDB

- Check MongoDB health: `docker compose logs mongodb`
- Verify the `depends_on` health check is passing: `docker compose ps mongodb`

### Port 80 already in use

Another service is using port 80. Stop it, or change the nginx port mapping in
`docker-compose.prod.yml` from `"80:80"` to e.g. `"8080:80"`.

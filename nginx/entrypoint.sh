#!/bin/sh
# nginx entrypoint — picks HTTP-only vs HTTPS config based on Let's Encrypt
# cert presence at runtime, then envsubst's ${DOMAIN} into the chosen template.
#
# This image is shared between dev and prod compose:
# - Dev: DOMAIN unset (defaults to "_" wildcard), no /etc/letsencrypt mount → HTTP-only.
# - Prod, before first cert: DOMAIN set, no cert files yet → HTTP-only with ACME path enabled.
# - Prod, after first cert: DOMAIN set, cert exists → HTTPS with HTTP→HTTPS redirect.
#
# A background watcher reloads nginx within ~5 minutes of cert renewal:
# certbot's deploy-hook touches /var/www/certbot/.cert-renewed; this loop
# detects the mtime change and signals nginx.
set -e

: "${DOMAIN:=_}"

CERT_PATH="/etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
TEMPLATE_HTTP="/etc/nginx/templates/nginx-http-only.conf.template"
TEMPLATE_HTTPS="/etc/nginx/templates/nginx-https.conf.template"
TARGET_CONF="/etc/nginx/conf.d/default.conf"
RELOAD_MARKER="/var/www/certbot/.cert-renewed"
LAST_RELOAD_FILE="/tmp/last-cert-reload-mtime"

if [ -f "$CERT_PATH" ]; then
    echo "[nginx-entrypoint] SSL cert found at $CERT_PATH — serving HTTPS for DOMAIN=${DOMAIN}"
    SOURCE_TEMPLATE="$TEMPLATE_HTTPS"
else
    echo "[nginx-entrypoint] No SSL cert at $CERT_PATH — HTTP-only bootstrap mode (DOMAIN=${DOMAIN})"
    SOURCE_TEMPLATE="$TEMPLATE_HTTP"
fi

# Substitute only ${DOMAIN}; leave $host, $uri etc. as nginx variables.
envsubst '${DOMAIN}' < "$SOURCE_TEMPLATE" > "$TARGET_CONF"

# Background renewal watcher — only meaningful when /var/www/certbot is mounted.
# Polls every 5 minutes; reloads nginx when the marker file's mtime changes.
(
    while true; do
        sleep 300
        [ -f "$RELOAD_MARKER" ] || continue
        MARKER_MTIME=$(stat -c %Y "$RELOAD_MARKER" 2>/dev/null || echo 0)
        LAST_MTIME=$(cat "$LAST_RELOAD_FILE" 2>/dev/null || echo 0)
        if [ "$MARKER_MTIME" -gt "$LAST_MTIME" ]; then
            echo "[nginx-watcher] cert renewal marker updated → nginx -s reload"
            nginx -s reload
            echo "$MARKER_MTIME" > "$LAST_RELOAD_FILE"
        fi
    done
) &

exec nginx -g "daemon off;"

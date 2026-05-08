# nginx/Dockerfile — builds the Vue SPA and serves it with nginx + reverse proxy config
#
# Build context must be the parent directory (set via docker-compose context: .)
# so both frontend/ and nginx/ are accessible.

# Stage 1: build the Vue frontend
FROM node:26-slim AS frontend-build

ARG VITE_TELEGRAM_BOT_NAME
ARG VITE_DEV_MODE
ENV VITE_TELEGRAM_BOT_NAME=${VITE_TELEGRAM_BOT_NAME}
ENV VITE_DEV_MODE=${VITE_DEV_MODE}

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: nginx with built SPA + runtime template selection (HTTP-only vs HTTPS)
FROM nginx:1.28-alpine

# envsubst (gettext) for ${DOMAIN} substitution at startup
RUN apk add --no-cache gettext

COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY nginx/templates/ /etc/nginx/templates/
COPY nginx/entrypoint.sh /coach-entrypoint.sh
RUN chmod +x /coach-entrypoint.sh

# Default conf is generated from templates by entrypoint at startup.
# Remove any stock conf so nginx doesn't try to load both.
RUN rm -f /etc/nginx/conf.d/default.conf

EXPOSE 80 443

# Pick HTTP-only or HTTPS template based on cert presence, then exec nginx.
ENTRYPOINT ["/coach-entrypoint.sh"]

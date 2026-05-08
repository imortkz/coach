# nginx/Dockerfile — builds the Vue SPA and serves it with nginx + reverse proxy config
#
# Build context must be the parent directory (set via docker-compose context: .)
# so both frontend/ and nginx/ are accessible.

# Stage 1: build the Vue frontend
FROM node:20-slim AS frontend-build

ARG VITE_TELEGRAM_BOT_NAME
ARG VITE_DEV_MODE
ENV VITE_TELEGRAM_BOT_NAME=${VITE_TELEGRAM_BOT_NAME}
ENV VITE_DEV_MODE=${VITE_DEV_MODE}

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: nginx with built SPA + reverse proxy config
FROM nginx:1.28-alpine
COPY --from=frontend-build /app/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

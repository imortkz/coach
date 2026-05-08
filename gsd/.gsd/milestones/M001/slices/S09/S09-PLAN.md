# S09: Docker Deployment

**Goal:** Docker Compose with nginx reverse proxy, FastAPI backend, and MongoDB for dev and production deployment.
**Demo:** docker-compose up starts 3 containers, app accessible in browser, MongoDB data survives restarts.

## Must-Haves
- docker-compose.yml defines 3 services: nginx, fastapi, mongodb
- nginx serves built Vue SPA and proxies /api/* to backend
- MongoDB data persists via Docker volume
- Production config ready for VPS deployment with bare IP

## Tasks
TBD — pending slice planning

## Files Likely Touched
- docker-compose.yml (new, at parent of repos)
- nginx/nginx.conf (new)
- backend/Dockerfile (update for MongoDB)
- frontend/Dockerfile (new, multi-stage build)
- .env.example (new)

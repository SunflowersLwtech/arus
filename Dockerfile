# Arus — Cloud Run multi-stage build
# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python runtime
FROM python:3.13-slim

WORKDIR /app

# Minimal OS deps for scipy / numpy wheels (some need libgomp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Python deps first — better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend
COPY backend/ ./backend/

# Copy frontend build artefacts (served as static files)
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Non-root user (Cloud Run best-practice)
RUN useradd --create-home --uid 1000 banjir && chown -R banjir /app
USER banjir

# Cloud Run injects PORT env var (typically 8080)
ENV PORT=8080
EXPOSE 8080

# Start: uvicorn bound to $PORT. Single worker because we share in-memory world.
# Cloud Run scales horizontally via instances, not workers; CPU=1, memory=1Gi recommended.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]

# =============================================================
# Mera Mentor - Single-service Dockerfile for Render
# Stage 1: Build React frontend
# Stage 2: FastAPI backend serves both API + React static files
# =============================================================

# ---- Stage 1: Build React ----
FROM node:18-slim AS frontend-builder

WORKDIR /frontend

# Install dependencies
COPY frontend/package.json frontend/yarn.lock ./
RUN yarn install --frozen-lockfile --network-timeout 300000

# Copy source
COPY frontend/ ./

# Build with empty BACKEND_URL so all API calls use same-origin /api/*
ENV REACT_APP_BACKEND_URL=""
ENV NODE_ENV=production
ENV DISABLE_ESLINT_PLUGIN=true

RUN yarn build

# ---- Stage 2: Python backend ----
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Backend source code
COPY backend/ ./

# React build output → /app/static/
COPY --from=frontend-builder /frontend/build ./static

# Render injects PORT; fall back to 8001 for local docker run
EXPOSE 8001

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT:-8001}"]

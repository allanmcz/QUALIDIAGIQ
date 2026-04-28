# syntax=docker/dockerfile:1.6
# Dockerfile multi-stage para QualiDiagIQ — Python 3.12 + FastAPI + WeasyPrint
# Otimizado para Apple Silicon M2 Max (linux/arm64) com fallback amd64.

# =========================
# Stage 1 — Base com deps
# =========================
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependências de sistema necessárias para WeasyPrint
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# =========================
# Stage 2 — Build deps Python
# =========================
FROM base AS builder

COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install --prefix=/install ".[dev]"

# =========================
# Stage 3 — Imagem final
# =========================
FROM base AS final

COPY --from=builder /install /usr/local

WORKDIR /app
COPY src/ ./src/

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()" || exit 1

CMD ["uvicorn", "src.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

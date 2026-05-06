# ─────────────────────────────────────────────────────────────
# CentauroADS Links — Dockerfile para Easypanel / DigitalOcean
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY app/ ./app/
COPY run.py .

# Directorio para SQLite
RUN mkdir -p /app/data

# Variables de entorno por defecto
ENV ADMIN_KEY=centauro2026
ENV DATABASE_URL=sqlite:///./data/centaurads_links.db

# Puerto (Easypanel usa 80 por defecto)
EXPOSE 8000
EXPOSE 8005

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8005/health || exit 1

# Iniciar
CMD ["python", "run.py"]

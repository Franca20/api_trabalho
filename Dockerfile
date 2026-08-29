FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_DATA_DIR=/tmp/api_trabalho_data

WORKDIR /app

# instalar dependências do sistema necessárias para builds (ajuste conforme seu requirements)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

# copiar requirements e instalar (uma camada só)
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# criar usuário não-root e ajustar permissões
RUN useradd --create-home appuser && \
    mkdir -p /tmp/api_trabalho_data && \
    chown -R appuser:appuser /tmp/api_trabalho_data /app
COPY --chown=appuser:appuser . .
USER appuser

EXPOSE 8000

# healthcheck simples (ajuste URL/porta conforme sua app)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:8000/health || exit 1

# gunicorn escuta 0.0.0.0 (recomendado)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000", "--workers", "3"]

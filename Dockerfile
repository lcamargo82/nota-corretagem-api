# Estágio Base
FROM python:3.11-slim AS base

# Configurações de ambiente Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Define diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para processamento de PDF e compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# --- Estágio de Desenvolvimento (com suporte a hot-reload) ---
FROM base AS development
ENV ENVIRONMENT=development
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# --- Estágio de Produção (otimizado e seguro) ---
FROM base AS production
ENV ENVIRONMENT=production
# Copia apenas o código fonte necessário da aplicação
COPY src/ ./src/
EXPOSE 8000
# Em produção, executa sem reload e pode utilizar múltiplos workers
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

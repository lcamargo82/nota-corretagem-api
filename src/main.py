import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.api.v1.api import api_router

# Configuração de Logging Global
logging.basicConfig(
    level=settings.LOG_LEVEL.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(
    title="Nota Corretagem API",
    description="Microsserviço Python/FastAPI para extração e normalização de dados financeiros de notas de corretagem (Padrão SINACOR). Suporta Day Trade e Swing Trade.",
    version="1.0.0"
)

# Configuração de CORS (Permite comunicação S2S segura)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão das rotas da API v1
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["Health"], summary="Verificar status da API")
def health_check():
    """Endpoint de verificação de vivacidade (health check) para orquestradores como Docker e Kubernetes."""
    return {
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "version": app.version
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=settings.PORT, reload=True)

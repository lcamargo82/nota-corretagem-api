from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Configurações globais da aplicação carregadas do arquivo .env.
    Utiliza Pydantic Settings para validação de tipos e valores padrão.
    """
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    LOG_LEVEL: str = "info"

    # Segurança JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"

    # Configuração Mistral AI
    MISTRAL_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

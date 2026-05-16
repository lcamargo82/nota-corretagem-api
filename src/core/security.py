import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.config import settings
import logging

security_scheme = HTTPBearer(
    scheme_name="JWT Bearer Token",
    description="Insira o token JWT no formato: Bearer <seu_token>"
)

def get_current_authorized_system(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """
    Dependência do FastAPI para validar o token JWT enviado no cabeçalho Authorization.
    Decodifica o token usando a chave secreta e algoritmo definidos nas configurações.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logging.warning("Tentativa de acesso com token JWT expirado.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT expirado. Solicite um novo token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logging.warning(f"Tentativa de acesso com token JWT inválido: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token JWT inválido ou corrompido.",
            headers={"WWW-Authenticate": "Bearer"},
        )

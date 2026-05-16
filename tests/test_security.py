import pytest
import jwt
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from src.core.config import settings
from src.core.security import get_current_authorized_system

def test_valid_jwt_token():
    """Testa se um token JWT válido é decodificado com sucesso pela dependência."""
    payload = {"sub": "test_system", "role": "admin"}
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    decoded = get_current_authorized_system(credentials)
    
    assert decoded["sub"] == "test_system"
    assert decoded["role"] == "admin"

def test_invalid_jwt_token():
    """Testa se um token JWT com assinatura inválida levanta a exceção correta (HTTP 401)."""
    payload = {"sub": "test_system"}
    # Assina com uma chave errada (mas com comprimento seguro > 32 bytes para evitar InsecureKeyLengthWarning)
    token = jwt.encode(payload, "wrong_secret_key_that_is_long_enough_32_bytes_min", algorithm=settings.JWT_ALGORITHM)
    
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_authorized_system(credentials)
        
    assert exc_info.value.status_code == 401
    assert "Token JWT inválido" in exc_info.value.detail

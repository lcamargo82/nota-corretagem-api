import pytest
import jwt
from fastapi.testclient import TestClient
from src.main import app
from src.core.config import settings

client = TestClient(app)

def gerar_token_valido():
    payload = {"sub": "sistema_teste", "role": "s2s"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_processar_nota_sem_token_deve_retornar_401():
    # Sem cabeçalho de autorização
    with open("Nota.pdf", "rb") as f:
        response = client.post(
            "/api/v1/notas/processar",
            files={"file": ("Nota.pdf", f, "application/pdf")}
        )
    assert response.status_code == 401

def test_processar_nota_arquivo_invalido():
    token = gerar_token_valido()
    response = client.post(
        "/api/v1/notas/processar",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("arquivo.txt", b"conteudo de texto", "text/plain")}
    )
    assert response.status_code == 400
    assert "não é um PDF válido" in response.json()["detail"]

def test_processar_nota_sucesso():
    token = gerar_token_valido()
    with open("Nota.pdf", "rb") as f:
        response = client.post(
            "/api/v1/notas/processar",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("Nota.pdf", f, "application/pdf")}
        )
    assert response.status_code == 200
    dados = response.json()
    assert dados["sucesso"] is True
    assert dados["dados"]["cabecalho"]["numero_nota"] == 125838

def test_processar_nota_protegida_sem_senha_retorna_422():
    token = gerar_token_valido()
    with open("NotaNegociacao-18526735-01-08-2025-31-08-2025-0.pdf", "rb") as f:
        response = client.post(
            "/api/v1/notas/processar",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("NotaNegociacao.pdf", f, "application/pdf")}
        )
    assert response.status_code == 422
    assert "PDF protegido por senha" in response.json()["detail"]

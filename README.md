# 📊 Nota Corretagem API (Day Trade Parser)

> Microsserviço de alta performance em Python (FastAPI) e Docker para ingestão, extração estruturada e normalização de notas de corretagem de Day Trade (Padrão SINACOR).

---

## 📖 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura e Tecnologias](#-arquitetura-e-tecnologias)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Executando a Aplicação (Docker)](#-executando-a-aplicação-docker)
  - [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento-dev)
  - [Ambiente de Produção](#ambiente-de-produção-prod)
- [Documentação da API e Endpoints](#-documentação-da-api-e-endpoints)
- [Exemplo de Uso com cURL](#-exemplo-de-uso-com-curl)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Testes e Validação](#-testes-e-validação)

---

## 🚀 Visão Geral

A **Nota Corretagem API** atua como um motor de extração financeiro independente. Projetada para integrar-se ao ecossistema de microsserviços da plataforma principal, ela recebe arquivos PDF de notas de corretagem, realiza o parse avançado via `pdfplumber` (Regex) com fallback inteligente para LLM (Ollama/Mistral) e retorna um JSON perfeitamente tipado e estruturado via Pydantic v2.

O microsserviço é protegido por autenticação JWT, garantindo comunicação segura entre sistemas (S2S), e isola completamente credenciais de IA no arquivo `.env`.

---

## 🛠 Arquitetura e Tecnologias

- **Linguagem:** Python 3.11+
- **Framework Web:** FastAPI (Alta performance, suporte nativo a Async e OpenAPI)
- **Validação e Contratos:** Pydantic v2 & Pydantic Settings
- **Processamento de PDF:** `pdfplumber` e `pypdf`
- **Motor de IA (Fallback):** Ollama (Local) e Mistral AI API (Nuvem)
- **Segurança:** Autenticação JWT (`PyJWT`), proteção de segredos via `.env`
- **DevOps:** Docker e Docker Compose (Multi-stage build)

---

## 📋 Pré-requisitos

Antes de iniciar, certifique-se de ter instalado em sua máquina:
- [Docker](https://www.docker.com/) (v24.0+)
- [Docker Compose](https://docs.docker.com/compose/) (v2.0+)
- [Git](https://git-scm.com/)

---

## ⚙️ Instalação e Configuração

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/sua-org/nota-corretagem-api.git
   cd nota-corretagem-api
   ```

2. **Crie o arquivo de variáveis de ambiente:**
   Copie o template `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```

3. **Configure as variáveis no `.env`:**
   Abra o arquivo `.env` em seu editor e defina os valores adequados:
   ```bash
   # Configurações do Servidor
   ENVIRONMENT=development # ou production
   PORT=8000
   LOG_LEVEL=info

   # Segurança JWT (Chave utilizada para validar os tokens do sistema chamador)
   JWT_SECRET_KEY=sua_chave_secreta_jwt_super_segura_aqui
   JWT_ALGORITHM=HS256

   # Configurações de IA (Fallback)
   # Nota: No Docker para Mac/Windows, use http://host.docker.internal:11434 para acessar o Ollama da máquina host
   OLLAMA_BASE_URL=http://host.docker.internal:11434
   MISTRAL_API_KEY=sua_api_key_da_mistral_aqui
   ```

---

## 🐳 Executando a Aplicação (Docker)

O projeto inclui configurações completas de Docker Compose para os ambientes de desenvolvimento e produção.

### Ambiente de Desenvolvimento (`dev`)

No modo de desenvolvimento, a aplicação é montada com volumes locais, permitindo o *hot-reload* (atualização automática do servidor ao salvar arquivos de código).

```bash
# Iniciar o container em modo interativo com hot-reload
docker compose up --build
```
A API estará disponível em: `http://localhost:8000`  
A documentação interativa (Swagger UI) estará em: `http://localhost:8000/docs`

### Ambiente de Produção (`prod`)

No modo de produção, a aplicação utiliza a imagem otimizada multi-stage e executa o servidor Uvicorn com múltiplos workers para altíssimo throughput, sem montagem de volumes de código local.

```bash
# Iniciar em modo daemon (background) usando o override de produção
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Para visualizar os logs do container em produção:
```bash
docker compose logs -f app
```

---

## 🔌 Documentação da API e Endpoints

A documentação interativa da API é gerada automaticamente pelo FastAPI (OpenAPI/Swagger) e pode ser acessada pelo navegador quando o servidor estiver rodando:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Endpoint Principal: Importar Nota

- **Método:** `POST`
- **Rota:** `/api/v1/notas/importar`
- **Autenticação:** Obrigatória (`Bearer Token` JWT)
- **Content-Type:** `multipart/form-data`

---

## 💻 Exemplo de Uso com cURL

Para simular a requisição feita pelo sistema chamador, utilize o comando `curl` abaixo. Substitua `SEU_TOKEN_JWT_AQUI` por um token válido e aponte para um arquivo PDF real.

```bash
curl -X POST "http://localhost:8000/api/v1/notas/importar" \
  -H "Authorization: Bearer SEU_TOKEN_JWT_AQUI" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./Nota.pdf;type=application/pdf" \
  -F "provider=ollama" \
  -F "model_name=mistral"
```

### Resposta de Sucesso Esperada (JSON)

```json
{
  "sucesso": true,
  "ambiente": "development",
  "dados": {
    "cabecalho": {
      "numero_nota": 987654,
      "data_pregao": "2026-05-16",
      "cpf_cliente": "123.456.789-00",
      "corretora_nome": "XP INVESTIMENTOS CCTVM S/A"
    },
    "operacoes": [
      {
        "tipo_operacao": "C",
        "mercado": "VISTA",
        "ativo": "VALE3",
        "quantidade": 1000,
        "preco_unitario": 62.30,
        "valor_total": 62300.00,
        "debito_credito": "D"
      },
      {
        "tipo_operacao": "V",
        "mercado": "VISTA",
        "ativo": "VALE3",
        "quantidade": 1000,
        "preco_unitario": 63.00,
        "valor_total": 63000.00,
        "debito_credito": "C"
      }
    ],
    "resumo_financeiro": {
      "taxa_liquidacao": 16.50,
      "emolumentos": 11.20,
      "taxa_corretagem": 0.00,
      "iss": 0.00,
      "irrf_dedo_duro": 7.00,
      "valor_liquido_nota": 665.30
    }
  }
}
```

---

## 📁 Estrutura do Projeto

```plaintext
nota-corretagem-api/
├── src/
│   ├── main.py                 # Setup do FastAPI e rotas principais
│   ├── core/
│   │   ├── config.py           # Configurações com Pydantic Settings
│   │   └── security.py         # Middleware/Dependência de validação JWT
│   ├── api/
│   │   └── v1/endpoints/
│   │       └── notas.py        # Rota POST /importar
│   ├── schemas/
│   │   └── nota.py             # Schemas de validação de Input/Output (Pydantic v2)
│   ├── services/
│   │   ├── processor.py        # Orquestrador do fluxo de extração
│   │   ├── extractors.py       # Extração via pdfplumber e Regex
│   │   └── llm_engine.py       # Integração com Ollama e Mistral API
│   └── utils/
│       └── financial.py        # Cálculos de ajuste de Mercado Futuro (WIN/WDO)
├── Dockerfile                  # Manifesto de construção Docker
├── docker-compose.yml          # Orquestrador Docker Compose
└── requirements.txt            # Dependências do Python
```

---

## 🧪 Testes e Validação

O projeto utiliza `pytest` para testes unitários e de integração, garantindo que o parser Regex e as validações Pydantic funcionem perfeitamente.

Para executar a suíte de testes localmente dentro do container Docker:

```bash
# Executar o pytest dentro do container em execução
docker compose exec app pytest -v
```

Para rodar a verificação de cobertura de código (coverage):
```bash
docker compose exec app pytest --cov=src --cov-report=term-missing
```

---

## 🛡️ Licença e Suporte

Este projeto é um software proprietário desenvolvido para o ecossistema interno da plataforma. Todos os direitos reservados.

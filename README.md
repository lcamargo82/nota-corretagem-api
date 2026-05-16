# 📊 Nota Corretagem API (Day Trade & Swing Trade Parser)

> Microsserviço de alta performance em Python (FastAPI) e Docker para ingestão, extração estruturada e normalização de notas de corretagem (Padrão SINACOR), com suporte a PDFs protegidos por senha e fallback inteligente de IA.

---

## 📖 Índice

- [Visão Geral](#-visão-geral)
- [Arquitetura e Tecnologias](#-arquitetura-e-tecnologias)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Executando a Aplicação (Docker)](#-executando-a-aplicação-docker)
  - [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento-dev)
  - [Ambiente de Produção](#ambiente-de-produção-prod)
- [Guia de Integração para Outros Sistemas (S2S)](#-guia-de-integração-para-outros-sistemas-s2s)
  - [Fluxo de Autenticação JWT](#1-fluxo-de-autenticação-jwt)
  - [Tratamento de PDFs com Senha](#2-tratamento-de-pdfs-com-senha)
  - [Segregação Day Trade e Swing Trade](#3-segregação-day-trade-e-swing-trade)
- [Documentação da API e Endpoints](#-documentação-da-api-e-endpoints)
- [Exemplo de Uso com cURL](#-exemplo-de-uso-com-curl)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Testes e Validação](#-testes-e-validação)

---

## 🚀 Visão Geral

A **Nota Corretagem API** atua como um motor de extração financeiro independente. Projetada para integrar-se ao ecossistema de microsserviços da plataforma principal, ela recebe arquivos PDF de notas de corretagem (inclusive arquivos protegidos por senha), realiza o parse avançado via `pdfplumber` (Regex) com fallback inteligente para a API em nuvem da **Mistral AI** e retorna um JSON perfeitamente tipado e estruturado via Pydantic v2.

O microsserviço é protegido por autenticação JWT, garantindo comunicação segura entre sistemas (S2S), e isola completamente credenciais de IA no arquivo `.env`.

---

## 🛠 Arquitetura e Tecnologias

- **Linguagem:** Python 3.11+
- **Framework Web:** FastAPI (Alta performance, suporte nativo a Async e OpenAPI)
- **Validação e Contratos:** Pydantic v2 & Pydantic Settings
- **Processamento de PDF:** `pdfplumber` e `pypdf` (com suporte a descriptografia)
- **Motor de IA (Fallback):** Mistral AI API (Nuvem)
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

   # Configurações de IA (Fallback Exclusivo Mistral AI)
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

## 🔗 Guia de Integração para Outros Sistemas (S2S)

Este microsserviço foi desenhado para ser consumido por outros backends do ecossistema. Abaixo estão as diretrizes para uma integração robusta e segura.

### 1. Fluxo de Autenticação JWT

Todas as requisições para a API devem incluir um token JWT válido no cabeçalho `Authorization`. 
- **Formato:** `Authorization: Bearer <SEU_TOKEN_JWT>`
- O token deve ser assinado com a mesma `JWT_SECRET_KEY` e algoritmo (`JWT_ALGORITHM`) configurados no `.env` da API de Notas.
- **Payload Recomendado do Token:**
  ```json
  {
    "sub": "backend-principal",
    "role": "service",
    "exp": 1779000000
  }
  ```

### 2. Tratamento de PDFs com Senha

Muitas corretoras enviam notas de corretagem protegidas pela senha do cliente (frequentemente o CPF ou data de nascimento).
- O sistema chamador deve verificar se o PDF exige senha ou solicitar a senha ao usuário final.
- Ao fazer o upload para a API de Notas, envie a senha no campo `password` do form-data.
- **Comportamento da API:** Se o arquivo for protegido e o campo `password` não for enviado (ou estiver incorreto), a API retornará o status **422 Unprocessable Entity** com a mensagem `PDF protegido por senha. Forneça a senha correta no campo 'password'`.

### 3. Segregação Day Trade e Swing Trade

O contrato de resposta da API de Notas devolve cada operação com a flag `modalidade` (`DAY_TRADE` ou `SWING_TRADE`).
- O backend chamador deve utilizar essa classificação ao salvar no banco de dados para garantir que o cálculo de imposto de renda aplique as alíquotas corretas (20% para Day Trade, 15% para Swing Trade) e respeite a regra de isenção de R$ 20 mil mensais exclusiva para vendas de ações em Swing Trade.

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

Para simular a requisição feita pelo sistema chamador (enviando um PDF protegido por senha), utilize o comando `curl` abaixo:

```bash
curl -X POST "http://localhost:8000/api/v1/notas/importar" \
  -H "Authorization: Bearer SEU_TOKEN_JWT_AQUI" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@./NotaNegociacao-18526735-01-08-2025-31-08-2025-0.pdf;type=application/pdf" \
  -F "password=senha_do_pdf_aqui" \
  -F "model_name=mistral-tiny"
```

### Resposta de Sucesso Esperada (JSON)

```json
{
  "sucesso": true,
  "ambiente": "development",
  "dados": {
    "cabecalho": {
      "numero_nota": 18526735,
      "data_pregao": "2025-08-01",
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
        "debito_credito": "D",
        "modalidade": "SWING_TRADE"
      },
      {
        "tipo_operacao": "V",
        "mercado": "VISTA",
        "ativo": "PETR4",
        "quantidade": 1000,
        "preco_unitario": 38.00,
        "valor_total": 38000.00,
        "debito_credito": "C",
        "modalidade": "DAY_TRADE"
      }
    ],
    "resumo_financeiro": {
      "taxa_liquidacao": 16.50,
      "emolumentos": 11.20,
      "taxa_corretagem": 0.00,
      "iss": 0.00,
      "irrf_day_trade": 5.00,
      "irrf_swing_trade": 1.90,
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
│   │   ├── extractors.py       # Extração via pdfplumber (com suporte a senha) e Regex
│   │   └── llm_engine.py       # Integração com Mistral API
│   └── utils/
│       └── financial.py        # Cálculos de ajuste e classificação Day/Swing Trade
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

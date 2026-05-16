# System Specification Document (SSD) - API de Importação de Notas de Corretagem (Day Trade & Swing Trade)

## 1. Visão Geral da Arquitetura

O microsserviço **Nota Corretagem API** segue uma arquitetura limpa e modular em Python 3.11+, utilizando o framework **FastAPI** para exposição de endpoints REST de alta performance e **Pydantic v2** para validação estrita de contratos de dados.

O design do sistema prioriza a separação de conceitos (SoC - Separation of Concerns), isolando completamente a camada de transporte HTTP (rotas e controllers) da camada de regras de negócio e extração de PDF (services e extractors). Essa abordagem garante que o sistema opere inicialmente no modelo síncrono (Request $\rightarrow$ Response), mas esteja estruturalmente pronto para ser acoplado a mensagerias assíncronas (como Celery ou ARQ) sem modificação no código de negócio. O motor de IA de fallback utiliza exclusivamente a API em nuvem da **Mistral AI**.

---

## 2. Diagrama de Arquitetura e Fluxo de Execução

O fluxo de processamento de uma nota de corretagem (com suporte a senha e fallback Mistral API) ocorre conforme o diagrama de sequência abaixo:

```mermaid
sequenceDiagram
    autonumber
    actor Cliente as Sistema Chamador (Backend)
    participant API as FastAPI (Controller)
    participant Auth as AuthService (JWT Middleware)
    participant Proc as NoteProcessorService
    participant PDF as PDFExtractor (pdfplumber / Regex)
    participant LLM as MistralAIEngine (Nuvem)

    Cliente->>API: POST /api/v1/notas/importar (PDF + Senha Opcional + JWT Bearer)
    API->>Auth: Validar Token JWT
    alt Token Inválido / Expirado
        Auth-->>API: Exceção HTTP 401 Unauthorized
        API-->>Cliente: Erro HTTP 401
    else Token Válido
        Auth-->>API: Usuário / Sistema Autorizado
        API->>Proc: processar_nota_pdf(arquivo_pdf, password, model_name)
        Proc->>PDF: extrair_texto_e_parse_regex(arquivo_pdf, password)
        
        alt Senha Incorreta / PDF Protegido
            PDF-->>Proc: Exceção de Descriptografia
            Proc-->>API: Exceção HTTP 422 / 400 (Senha Inválida)
            API-->>Cliente: Erro HTTP 422 (Senha Obrigatória ou Incorreta)
        else Leitura com Sucesso
            PDF-->>Proc: Dados Estruturados (Caminho Feliz)
            
            alt Falha no Regex / PDF Escaneado
                Proc->>LLM: extrair_transacoes_mistral(texto_pdf ou imagem, model_name)
                LLM-->>Proc: JSON Estruturado via Mistral API
            end

            Proc->>Proc: Classificar Day Trade / Swing Trade e Validar Pydantic v2
            Proc-->>API: NotaCorretagemResponse (DTO)
            API-->>Cliente: HTTP 200 OK (JSON Payload)
        end
    end
```

---

## 3. Estrutura de Diretórios do Projeto

A organização interna do repositório segue o padrão modular para microsserviços escaláveis em FastAPI:

```plaintext
nota-corretagem-api/
├── Dockerfile                  # Manifesto de construção da imagem Docker (Multi-stage)
├── docker-compose.yml          # Orquestração de containers para Dev e Prod
├── requirements.txt            # Dependências de produção do projeto
├── README.md                   # Documentação de instalação e uso
├── prd.md                      # Product Requirements Document
├── ssd.md                      # System Specification Document (Este arquivo)
├── .env.example                # Template de variáveis de ambiente
├── docs/
│   └── PLAN-nota-corretagem-api.md # Plano de execução detalhado
└── src/
    ├── __init__.py
    ├── main.py                 # Ponto de entrada da aplicação FastAPI
    ├── core/
    │   ├── __init__.py
    │   ├── config.py           # Gestão de configurações e variáveis de ambiente (Pydantic Settings)
    │   └── security.py         # Middlewares e utilitários de validação JWT
    ├── api/
    │   ├── __init__.py
    │   ├── v1/
    │   │   ├── __init__.py
    │   │   └── endpoints/
    │   │       ├── __init__.py
    │   │       └── notas.py    # Rotas HTTP REST para importação de notas
    ├── schemas/
    │   ├── __init__.py
    │   └── nota.py             # Schemas Pydantic v2 (Input, Output, DTOs com suporte a Day/Swing Trade)
    ├── services/
    │   ├── __init__.py
    │   ├── processor.py        # Serviço orquestrador de extração e validação de notas
    │   ├── extractors.py       # Lógica de extração via pdfplumber (com suporte a senha) e Regex
    │   └── llm_engine.py       # Cliente de integração com a API da Mistral AI
    └── utils/
        ├── __init__.py
        └── financial.py        # Utilitários de conversão financeira e segregação de modalidades
```

---

## 4. Especificação da API REST (Contrato de Dados)

### Endpoint: Importar Nota de Corretagem

- **Rota:** `POST /api/v1/notas/importar`
- **Autenticação:** Obrigatória (`Bearer Token` JWT no header `Authorization`).
- **Content-Type:** `multipart/form-data`

#### Parâmetros da Requisição (Form Data)

| Campo | Tipo | Obrigatório | Descrição |
| :--- | :--- | :---: | :--- |
| `file` | `UploadFile` | Sim | Arquivo PDF da nota de corretagem (padrão SINACOR). |
| `password` | `str` | Não | Senha de abertura para PDFs protegidos/criptografados. |
| `model_name` | `str` | Não | Nome do modelo Mistral para fallback (ex: `mistral-tiny`, `mistral-small`). |

#### Exemplo de Payload de Resposta (HTTP 200 OK)

```json
{
  "sucesso": true,
  "ambiente": "producao",
  "dados": {
    "cabecalho": {
      "numero_nota": 18526735,
      "data_pregao": "2025-08-01",
      "cpf_cliente": "111.222.333-44",
      "corretora_nome": "XP INVESTIMENTOS CCTVM S/A"
    },
    "operacoes": [
      {
        "tipo_operacao": "C",
        "mercado": "VISTA",
        "ativo": "PETR4",
        "quantidade": 500,
        "preco_unitario": 38.50,
        "valor_total": 19250.00,
        "debito_credito": "D",
        "modalidade": "DAY_TRADE"
      },
      {
        "tipo_operacao": "V",
        "mercado": "VISTA",
        "ativo": "PETR4",
        "quantidade": 500,
        "preco_unitario": 39.00,
        "valor_total": 19500.00,
        "debito_credito": "C",
        "modalidade": "DAY_TRADE"
      },
      {
        "tipo_operacao": "C",
        "mercado": "VISTA",
        "ativo": "VALE3",
        "quantidade": 300,
        "preco_unitario": 60.00,
        "valor_total": 18000.00,
        "debito_credito": "D",
        "modalidade": "SWING_TRADE"
      }
    ],
    "resumo_financeiro": {
      "taxa_liquidacao": 10.20,
      "emolumentos": 6.80,
      "taxa_corretagem": 0.00,
      "iss": 0.00,
      "irrf_day_trade": 2.50,
      "irrf_swing_trade": 0.00,
      "valor_liquido_nota": 222.50
    }
  }
}
```

#### Tratamento de Erros (HTTP Status Codes)

- **400 Bad Request:** Arquivo enviado não é um PDF ou o PDF está corrompido/vazio.
- **401 Unauthorized:** Token JWT ausente, inválido ou expirado.
- **422 Unprocessable Entity:** Erro de validação de parâmetros ou PDF protegido por senha cuja senha não foi fornecida (ou está incorreta).
- **500 Internal Server Error:** Falha inesperada no processamento de extração ou na Mistral API.

---

## 5. Modelagem de Dados Sugerida para o Banco Cliente

Para garantir a preservação do histórico fiscal e a capacidade de segregar apurações de Day Trade e Swing Trade, o sistema chamador deve adotar uma estrutura normalizada no seu banco de dados relacional (PostgreSQL/MySQL), conforme sugerido abaixo:

```mermaid
erDiagram
    NOTAS_CORRETAGEM ||--|{ OPERACOES_NOTA : possui
    NOTAS_CORRETAGEM ||--|| CUSTOS_NOTA : possui

    NOTAS_CORRETAGEM {
        UUID id PK
        INT numero_nota
        VARCHAR corretora_id
        VARCHAR user_id
        DATE data_pregao
        VARCHAR hash_arquivo "Índice único para evitar duplicidade"
        TIMESTAMP created_at
    }

    OPERACOES_NOTA {
        UUID id PK
        UUID nota_id FK
        VARCHAR tipo_ordem "C ou V"
        VARCHAR mercado "VISTA, FUTURO, OPCOES"
        VARCHAR ativo "Ticker (ex: PETR4, WDOJ26)"
        INT quantidade
        DECIMAL preco_unitario
        DECIMAL valor_total
        VARCHAR debito_credito "D ou C"
        VARCHAR modalidade "DAY_TRADE ou SWING_TRADE"
    }

    CUSTOS_NOTA {
        UUID id PK
        UUID nota_id FK
        DECIMAL taxa_liquidacao
        DECIMAL emolumentos
        DECIMAL corretagem
        DECIMAL iss
        DECIMAL irrf_day_trade "1% retido na fonte"
        DECIMAL irrf_swing_trade "0,005% retido na fonte"
        DECIMAL valor_liquido_nota
    }
```

---

## 6. Estratégia de Conteinerização e DevOps

O projeto adota Docker para garantir paridade entre os ambientes de desenvolvimento e produção, seguindo as melhores práticas de segurança e otimização de imagem.

### Dockerfile Multi-stage
O manifesto Docker utiliza um build multi-stage baseado na imagem oficial `python:3.11-slim`. A primeira etapa compila as dependências do sistema (como drivers para compilação de pacotes C e ferramentas de PDF), enquanto a imagem final contém apenas os artefatos compilados e o código da aplicação, reduzindo drasticamente a superfície de ataque e o tamanho do container.

### Docker Compose
O orquestrador `docker-compose.yml` expõe a aplicação na porta `8000` e gerencia as variáveis de ambiente essenciais. No ambiente de produção, a aplicação é executada via Uvicorn/Gunicorn com múltiplos workers para maximizar o throughput de requisições concorrentes.

---

## 7. Segurança e Gestão de Segredos

### Blindagem do `.env`
O sistema utiliza `pydantic-settings` para carregar e validar as variáveis de ambiente na inicialização da aplicação. O arquivo `.env` deve conter as seguintes chaves essenciais:

```bash
# Configurações da Aplicação
ENVIRONMENT=development
PORT=8000
LOG_LEVEL=info

# Segurança JWT
JWT_SECRET_KEY=sua_chave_secreta_jwt_super_segura_aqui
JWT_ALGORITHM=HS256

# Configurações de IA (Fallback Exclusivo Mistral AI)
MISTRAL_API_KEY=sua_api_key_da_mistral_aqui
```

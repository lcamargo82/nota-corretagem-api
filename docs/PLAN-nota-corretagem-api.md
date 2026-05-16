# Plano de Projeto - API de Importação de Notas de Corretagem (Day Trade & Swing Trade)

## 1. Overview

Este documento estabelece o plano arquitetural e de execução para a construção da **Nota Corretagem API**, um microsserviço Python conteinerizado com Docker, focado no processamento e normalização de notas de corretagem do mercado financeiro brasileiro (padrão SINACOR), com suporte a operações de **Day Trade** e **Swing Trade**.

A API receberá arquivos PDF (com suporte a senhas para arquivos protegidos) de um sistema cliente via requisições HTTP REST protegidas por JWT, extrairá os dados de cabeçalho, operações (identificando a modalidade) e resumo financeiro (taxas, emolumentos, IRRF) utilizando um motor híbrido de alta velocidade (`pdfplumber` + Regex) com fallback inteligente exclusivo para a API em nuvem da **Mistral AI**, e retornará um payload JSON perfeitamente tipado via Pydantic v2. A persistência em banco de dados será realizada pelo sistema cliente.

---

## 2. Project Type

**BACKEND** (Microsserviço de Extração e Ingestão de Dados).

> **Agente Primário Alocado:** `backend-specialist` (com suporte de `security-auditor` para validações de JWT e segredos, e `devops-engineer` para Docker e versionamento Git).

---

## 3. Success Criteria

- **Critério 1 (Ingestão com Senha e Validação JWT):** Endpoint `POST /api/v1/notas/importar` funcional, aceitando arquivos PDF e campo opcional `password` via form-data, e validando corretamente a presença e validade do token JWT no header `Authorization`.
- **Critério 2 (Precisão do Parser SINACOR com Senha):** Motor de extração Regex/pdfplumber capturando 100% dos campos de cabeçalho, tabela de negócios e rodapé financeiro nas 4 notas de referência da raiz, abrindo com sucesso a nota protegida por senha.
- **Critério 3 (Suporte a Day Trade e Swing Trade):** Contratos Pydantic e motor de extração identificando e segregando corretamente operações iniciadas e encerradas no mesmo dia (Day Trade) daquelas mantidas em carteira (Swing Trade).
- **Critério 4 (Fallback Mistral API Resiliente):** Integração exclusiva com a Mistral API em nuvem implementada e funcional para cenários de falha do Regex ou PDFs escaneados.
- **Critério 5 (Conteinerização e Paridade):** Arquivos `Dockerfile` (multi-stage) e `docker-compose.yml` funcionais para os modos de desenvolvimento (`dev` com hot-reload) e produção (`prod` otimizado).

---

## 4. Tech Stack

| Tecnologia | Função / Rationale |
| :--- | :--- |
| **Python 3.11+** | Linguagem base, oferecendo excelente ecossistema para manipulação de PDFs e IA. |
| **FastAPI** | Framework web de altíssima performance, suporte nativo a concorrência (async/sync) e OpenAPI. |
| **Pydantic v2 & Settings** | Validação estrita de contratos de dados (Input/Output) e gestão segura de variáveis de ambiente (`.env`). |
| **pdfplumber & pypdf** | Ferramentas de extração de texto e layout de PDFs com suporte nativo a descriptografia por senha. |
| **PyJWT & Cryptography** | Implementação de segurança para verificação e decodificação de tokens JWT. |
| **Requests / MistralAI** | Cliente HTTP para comunicação com a API em nuvem da Mistral AI. |
| **Docker & Compose** | Empacotamento, isolamento de ambiente e orquestração de serviços para dev e prod. |
| **Pytest & Coverage** | Suíte de testes unitários e de integração para validação cont뜛nua do parser. |

---

## 5. File Structure

```plaintext
nota-corretagem-api/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── requirements.txt
├── README.md
├── prd.md
├── ssd.md
├── .env.example
├── docs/
│   └── PLAN-nota-corretagem-api.md (Este arquivo)
└── src/
    ├── __init__.py
    ├── main.py
    ├── core/
    │   ├── __init__.py
    │   ├── config.py
    │   └── security.py
    ├── api/
    │   ├── __init__.py
    │   └── v1/endpoints/
    │       ├── __init__.py
    │       └── notas.py
    ├── schemas/
    │   ├── __init__.py
    │   └── nota.py
    ├── services/
    │   ├── __init__.py
    │   ├── processor.py
    │   ├── extractors.py
    │   └── llm_engine.py
    └── utils/
        ├── __init__.py
        └── financial.py
```

---

## 6. Task Breakdown

### Tarefa 1: Configuração Base, Pydantic Settings e Segurança JWT
- **ID:** `TASK-01`
- **Agente:** `backend-specialist` | **Skill:** `api-patterns`, `python-patterns`
- **Descrição:** Criar a estrutura inicial de diretórios, `requirements.txt`, `.env.example`, `src/core/config.py` para carregamento de variáveis de ambiente e `src/core/security.py` contendo a dependência FastAPI para validação do token JWT.
- **INPUT:** Arquivo `.env.example` com chaves de configuração.
- **OUTPUT:** Módulos `config.py` e `security.py` implementados e validados.
- **VERIFY:** Executar teste unitário confirmando que requisições com tokens JWT válidos passam pela dependência e tokens inválidos levantam `HTTPException(401)`.

### Tarefa 2: Schemas Pydantic v2 (Contratos com Day/Swing Trade)
- **ID:** `TASK-02`
- **Agente:** `backend-specialist` | **Skill:** `python-patterns`
- **Descrição:** Desenvolver os schemas em `src/schemas/nota.py` representando o cabeçalho (`CabecalhoNota`), as operações com a flag de modalidade (`OperacaoNota`), o resumo financeiro com IRRF segregado (`ResumoFinanceiro`) e o DTO de resposta final (`NotaCorretagemResponse`).
- **INPUT:** Especificação de campos do PRD/SSD atualizados.
- **OUTPUT:** Arquivo `src/schemas/nota.py` perfeitamente tipado com validadores internos.
- **VERIFY:** Instanciar objetos de teste garantindo que validações de modalidade (`DAY_TRADE` / `SWING_TRADE`) e valores monetários funcionam corretamente.

### Tarefa 3: Motor de Extração de PDF com Suporte a Senha (pdfplumber + Regex)
- **ID:** `TASK-03`
- **Agente:** `backend-specialist` | **Skill:** `python-patterns`
- **Descrição:** Implementar `src/services/extractors.py` contendo a classe `PDFProcessor` para abertura de PDFs (utilizando o parâmetro `password`) e parse via expressões regulares (Regex) focadas no padrão SINACOR.
- **INPUT:** 4 PDFs de referência da raiz (incluindo o PDF protegido por senha).
- **OUTPUT:** Classe `PDFProcessor` capaz de extrair e descriptografar os blocos estruturados.
- **VERIFY:** Executar script de teste passando os 4 PDFs de referência (fornecendo a senha para o protegido) e confirmando a extração correta.

### Tarefa 4: Motor de LLM Fallback (Mistral API Exclusivo)
- **ID:** `TASK-04`
- **Agente:** `backend-specialist` | **Skill:** `python-patterns`
- **Descrição:** Criar `src/services/llm_engine.py` contendo a classe `LLMClient` para comunicação exclusiva com a Mistral API em nuvem, utilizando prompts estruturados para extração de transações quando o Regex falhar.
- **INPUT:** Texto bruto ou imagem de PDF escaneado.
- **OUTPUT:** Classe `LLMClient` funcional com tratamento de erros e resiliência.
- **VERIFY:** Simular chamada à Mistral API com texto de extrato e verificar retorno do JSON estruturado.

### Tarefa 5: Serviço Orquestrador e Classificação Day/Swing Trade
- **ID:** `TASK-05`
- **Agente:** `backend-specialist` | **Skill:** `python-patterns`
- **Descrição:** Implementar `src/services/processor.py` (`BankStatementProcessor`) e `src/utils/financial.py`. O orquestrador tentará o Regex primeiro (com senha), acionará a Mistral API se necessário, aplicará a classificação de Day Trade vs Swing Trade e validará contra os schemas Pydantic.
- **INPUT:** Arquivo PDF temporário, senha opcional e modelo Mistral.
- **OUTPUT:** Payload final normalizado no formato `NotaCorretagemResponse`.
- **VERIFY:** Processar um PDF completo ponta a ponta e validar a conformidade do payload gerado.

### Tarefa 6: Rotas FastAPI com Senha Opcional e Inicialização da Aplicação
- **ID:** `TASK-06`
- **Agente:** `backend-specialist` | **Skill:** `api-patterns`
- **Descrição:** Desenvolver `src/api/v1/endpoints/notas.py` com o endpoint `POST /importar` (aceitando `file`, `password` e `model_name`) e inicializar o app em `src/main.py`.
- **INPUT:** Serviços e dependências previamente criados.
- **OUTPUT:** Aplicação FastAPI completa e funcional.
- **VERIFY:** Acessar `http://localhost:8000/docs` e realizar requisição de teste via cURL ou Swagger UI.

### Tarefa 7: Conteinerização e Orquestração Docker
- **ID:** `TASK-07`
- **Agente:** `devops-engineer` | **Skill:** `docker-expert`, `deployment-procedures`
- **Descrição:** Criar o `Dockerfile` com multi-stage build otimizado para Python 3.11+ e os arquivos `docker-compose.yml` (desenvolvimento com hot-reload) e `docker-compose.prod.yml` (produção otimizada).
- **INPUT:** Aplicação FastAPI estruturada.
- **OUTPUT:** Manifestos Docker completos.
- **VERIFY:** Executar `docker compose up --build` e confirmar que o container sobe saudável.

---

## 7. Phase X: Verification

Esta fase garante a qualidade, segurança e corretude arquitetural do projeto antes da entrega final.

### Lista de Verificação (Checklist)

- [ ] **Verificação de Segurança (P0):** Nenhuma chave ou segredo hardcodado no código; uso estricto do `.env` e validação de JWT ativa nas rotas.
- [ ] **Qualidade de Código e Tipagem (P0):** Código seguindo padrões PEP8, sem erros de tipagem no Pydantic ou funções sem type hints.
- [ ] **Validação de Contrato de API (P1):** OpenAPI/Swagger UI gerado corretamente, refletindo suporte a senhas e modalidades.
- [ ] **Testes de Integração e Parser (P1):** Suíte de testes automatizados executando com sucesso contra as 4 notas de referência.
- [ ] **Auditoria Docker (P2):** Build multi-stage gerando imagem leve e segura.

### Comandos de Verificação Automatizada

```bash
# 1. Validação de Testes e Cobertura dentro do Container
docker compose exec app pytest -v --cov=src

# 2. Teste de Carga e Concorrência Básica (Simulação de Chamada Síncrona com Senha)
curl -X POST "http://localhost:8000/api/v1/notas/importar" \
  -H "Authorization: Bearer TOKEN_TESTE" \
  -F "file=@./NotaNegociacao-18526735-01-08-2025-31-08-2025-0.pdf" \
  -F "password=senha_correta"

# 3. Verificação de Logs e Saúde do Container
docker compose logs --tail=50 app
```

### Marcador de Conclusão da Fase X

```markdown
## ✅ PHASE X COMPLETE
- Segurança: ✅ Pass (Segredos no .env, JWT Ativo)
- Testes: ✅ Pass (100% das 4 notas de referência analisadas com sucesso)
- Docker: ✅ Pass (Containers Dev e Prod saudáveis)
- Data: [Data de Conclusão]
```

# Plano de Projeto - API de Importação de Notas de Corretagem (Day Trade)

## 1. Overview

Este documento estabelece o plano arquitetural e de execução para a construção da **Nota Corretagem API**, um microsserviço Python conteinerizado com Docker, focado no processamento e normalização de notas de corretagem Day Trade (padrão SINACOR).

A API receberá arquivos PDF de um sistema cliente via requisições HTTP REST protegidas por JWT, extrairá os dados de cabeçalho, operações e resumo financeiro (taxas, emolumentos, IRRF 1% "dedo-duro") utilizando um motor híbrido de alta velocidade (`pdfplumber` + Regex) com fallback inteligente para LLM (Ollama/Mistral), e retornará um payload JSON perfeitamente tipado via Pydantic v2. A persistência em banco de dados será realizada pelo sistema cliente, mantendo o microsserviço leve, veloz e puramente focado no parse.

---

## 2. Project Type

**BACKEND** (Microsserviço de Extração e Ingestão de Dados).

> **Agente Primário Alocado:** `backend-specialist` (com suporte de `security-auditor` para validações de JWT e segredos, e `test-engineer` para garantia de qualidade).

---

## 3. Success Criteria

- **Critério 1 (Ingestão e Validação):** Endpoint `POST /api/v1/notas/importar` funcional, aceitando arquivos PDF via form-data e validando corretamente a presença e validade do token JWT no header `Authorization`.
- **Critério 2 (Precisão do Parser SINACOR):** Motor de extração Regex/pdfplumber capturando 100% dos campos de cabeçalho, tabela de negócios e rodapé financeiro nas notas de referência (`Nota.pdf`, `Notas de Corretagem.pdf`, `NotaCM.pdf`).
- **Critério 3 (Fallback LLM Resiliente):** Integração com Ollama (Local) e Mistral API (Nuvem) implementada e funcional para cenários de falha do Regex ou PDFs escaneados.
- **Critério 4 (Validação Pydantic v2):** Retorno HTTP perfeitamente estruturado de acordo com os schemas Pydantic, garantindo tipagem forte e validação de regras financeiras (ex: cálculo de Mercado Futuro WIN/WDO).
- **Critério 5 (Conteinerização e Paridade):** Arquivos `Dockerfile` (multi-stage) e `docker-compose.yml` funcionais, permitindo inicialização limpa nos modos de desenvolvimento (`dev` com hot-reload) e produção (`prod` otimizado).

---

## 4. Tech Stack

| Tecnologia | Função / Rationale |
| :--- | :--- |
| **Python 3.11+** | Linguagem base, oferecendo excelente ecossistema para manipulação de PDFs e IA. |
| **FastAPI** | Framework web de altíssima performance, suporte nativo a concorrência (async/sync) e OpenAPI. |
| **Pydantic v2 & Settings** | Validação estrita de contratos de dados (Input/Output) e gestão segura de variáveis de ambiente (`.env`). |
| **pdfplumber & pypdf** | Ferramentas de extração de texto e layout de PDFs página a página com precisão de coordenadas. |
| **PyJWT & Cryptography** | Implementação de segurança para verificação e decodificação de tokens JWT. |
| **Requests / MistralAI** | Clientes HTTP para comunicação com o Ollama local e a API em nuvem da Mistral AI. |
| **Docker & Compose** | Empacotamento, isolamento de ambiente e orquestração de serviços para dev e prod. |
| **Pytest & Coverage** | Suíte de testes unitários e de integração para validação contínua do parser. |

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

### Tarefa 2: Schemas Pydantic v2 (Contratos de Dados)
- **ID:** `TASK-02`
- **Agente:** `backend-specialist` | **Skill:** `python-patterns`
- **Descrição:** Desenvolver os schemas em `src/schemas/nota.py` representando o cabeçalho (`CabecalhoNota`), as operações (`OperacaoNota`), o resumo financeiro (`ResumoFinanceiro`) e o DTO de resposta final (`NotaCorretagemResponse`).
- **INPUT:** Especificação de campos do PRD/SSD.
- **OUTPUT:** Arquivo `src/schemas/nota.py` perfeitamente tipado com validadores internos.
- **VERIFY:** Instanciar objetos de teste garantindo que validações de valores monetários e tipos de mercado funcionam corretamente.

### Tarefa 3: Motor de Extração de PDF (pdfplumber + Regex)
- **ID:** `TASK-03`
- **Agente:** `backend-specialist` | **Skill:** `python-patterns`
- **Descrição:** Implementar `src/services/extractors.py` contendo a classe `PDFProcessor` para leitura de páginas e parse via expressões regulares (Regex) focadas no padrão SINACOR.
- **INPUT:** PDFs de referência (`Nota.pdf`, `Notas de Corretagem.pdf`, `NotaCM.pdf`).
- **OUTPUT:** Classe `PDFProcessor` capaz de extrair os blocos estruturados.
- **VERIFY:** Executar script de teste passando os 3 PDFs de referência e confirmando a extração correta de 100% dos dados no caminho feliz.

### Tarefa 4: Motor de LLM Fallback (Ollama & Mistral API)
- **ID:** `TASK-04`
- **Agente:** `backend-specialist` | **Skill:** `python-patterns`
- **Descrição:** Criar `src/services/llm_engine.py` contendo a classe `LLMClient` para comunicação com Ollama (local) e Mistral API (nuvem), utilizando prompts estruturados para extração de transações quando o Regex falhar.
- **INPUT:** Texto bruto ou imagem de PDF escaneado.
- **OUTPUT:** Classe `LLMClient` funcional com tratamento de erros e resiliência.
- **VERIFY:** Simular chamada ao Ollama/Mistral com texto de extrato e verificar retorno do JSON estruturado.

### Tarefa 5: Serviço Orquestrador de Processamento e Cálculos Financeiros
- **ID:** `TASK-05`
- **Agente:** `backend-specialist` | **Skill:** `python-patterns`
- **Descrição:** Implementar `src/services/processor.py` (`BankStatementProcessor`) e `src/utils/financial.py`. O orquestrador tentará o Regex primeiro, acionará o LLM se necessário, aplicará os cálculos de ajuste BM&F (WIN/WDO) e validará contra os schemas Pydantic.
- **INPUT:** Arquivo PDF temporário e parâmetros de provedor.
- **OUTPUT:** Payload final normalizado no formato `NotaCorretagemResponse`.
- **VERIFY:** Processar um PDF completo ponta a ponta e validar a conformidade do payload gerado.

### Tarefa 6: Rotas FastAPI e Inicialização da Aplicação
- **ID:** `TASK-06`
- **Agente:** `backend-specialist` | **Skill:** `api-patterns`
- **Descrição:** Desenvolver `src/api/v1/endpoints/notas.py` com o endpoint `POST /importar` e inicializar o app em `src/main.py`, registrando roteadores, middlewares de CORS e tratamento de exceções.
- **INPUT:** Serviços e dependências previamente criados.
- **OUTPUT:** Aplicação FastAPI completa e funcional.
- **VERIFY:** Acessar `http://localhost:8000/docs` e realizar requisição de teste via cURL ou Swagger UI.

### Tarefa 7: Conteinerização e Orquestração Docker
- **ID:** `TASK-07`
- **Agente:** `devops-engineer` | **Skill:** `docker-expert`, `deployment-procedures`
- **Descrição:** Criar o `Dockerfile` com multi-stage build otimizado para Python 3.11+ e os arquivos `docker-compose.yml` (desenvolvimento com hot-reload) e `docker-compose.prod.yml` (produção otimizada).
- **INPUT:** Aplicação FastAPI estruturada.
- **OUTPUT:** Manifestos Docker completos.
- **VERIFY:** Executar `docker compose up --build` e confirmar que o container sobe saudável sem erros de inicialização.

---

## 7. Phase X: Verification

Esta fase garante a qualidade, segurança e corretude arquitetural do projeto antes da entrega final.

### Lista de Verificação (Checklist)

- [ ] **Verificação de Segurança (P0):** Nenhuma chave ou segredo hardcodado no código; uso estricto do `.env` e validação de JWT ativa nas rotas.
- [ ] **Qualidade de Código e Tipagem (P0):** Código seguindo padrões PEP8, sem erros de tipagem no Pydantic ou funções sem type hints.
- [ ] **Validação de Contrato de API (P1):** OpenAPI/Swagger UI gerado corretamente, refletindo esquemas de autenticação e modelos de resposta.
- [ ] **Testes de Integração e Parser (P1):** Suíte de testes automatizados executando com sucesso contra os PDFs de referência.
- [ ] **Auditoria Docker (P2):** Build multi-stage gerando imagem leve e segura, com volumes e portas configurados corretamente no Compose.

### Comandos de Verificação Automatizada

```bash
# 1. Validação de Testes e Cobertura dentro do Container
docker compose exec app pytest -v --cov=src

# 2. Teste de Carga e Concorrência Básica (Simulação de Chamada Síncrona)
curl -X POST "http://localhost:8000/api/v1/notas/importar" \
  -H "Authorization: Bearer TOKEN_TESTE" \
  -F "file=@./Nota.pdf"

# 3. Verificação de Logs e Saúde do Container
docker compose logs --tail=50 app
```

### Marcador de Conclusão da Fase X

```markdown
## ✅ PHASE X COMPLETE
- Segurança: ✅ Pass (Segredos no .env, JWT Ativo)
- Testes: ✅ Pass (100% dos PDFs de referência analisados com sucesso)
- Docker: ✅ Pass (Containers Dev e Prod saudáveis)
- Data: [Data de Conclusão]
```

# Product Requirements Document (PRD) - API de Importação de Notas de Corretagem (Day Trade)

## 1. Visão Geral do Produto

O **Nota Corretagem API** é um microsserviço especializado, desenvolvido em Python (FastAPI), conteinerizado via Docker, com o objetivo de realizar a ingestão, extração e normalização de dados de notas de corretagem de operações Day Trade no mercado financeiro brasileiro (padrão SINACOR).

A API foi projetada para atuar como um motor de extração desacoplado. Ela é consumida por outros sistemas do ecossistema via requisições HTTP REST autenticadas por tokens JWT. O sistema cliente envia o arquivo PDF da nota de corretagem, e a API devolve um payload JSON estruturado, contendo o cabeçalho da nota, a lista de operações (tabela de negócios) e o resumo financeiro detalhado (incluindo taxas, emolumentos e retenções de imposto como o IRRF "dedo-duro"). A persistência final desses dados no banco de dados relacional é responsabilidade do sistema cliente, garantindo uma arquitetura limpa e de microsserviços independentes.

---

## 2. Objetivos e Metas

- **Precisão Financeira Absoluta:** Garantir 100% de exatidão na extração de valores monetários, quantidades e identificação de débito/crédito (D/C).
- **Padronização SINACOR:** Suportar o padrão utilizado pela quase totalidade das corretoras brasileiras (XP, BTG, Clear, Rico, Genial, etc.).
- **Arquitetura de Alta Performance e Desacoplada:** Utilizar FastAPI com processamento síncrono (Request $\rightarrow$ Response) otimizado, mas com design interno preparado para fácil transição para processamento assíncrono baseado em filas (Celery/ARQ/RabbitMQ) no futuro.
- **Segurança e Blindagem de Credenciais:** Proteger o acesso à API via autenticação JWT e isolar credenciais de IA (como o token do Ollama/Mistral) no arquivo `.env`, sem exposição nos payloads ou logs.

---

## 3. Personas e Usuários

1. **Sistema Chamador (Backend Consumidor):** Aplicação principal do ecossistema que gerencia o usuário final, armazena o histórico no banco de dados e solicita o parse do PDF.
2. **Investidor / Trader (Usuário Final do Sistema Principal):** Realiza operações Day Trade (Ações e Mercado Futuro BM&F) e necessita da importação automatizada de suas notas para cálculo de DARF e acompanhamento de métricas.
3. **Auditoria Fiscal (Receita Federal / Malha Fina):** Requer rastreabilidade completa entre o lucro bruto, as taxas operacionais dedutíveis e o IRRF retido na fonte.

---

## 4. Requisitos Funcionais (RF)

### RF01 - Ingestão e Validação de Arquivo
- A API deve disponibilizar um endpoint `POST /api/v1/notas/importar` que aceite arquivos no formato PDF via `multipart/form-data`.
- O sistema deve validar a extensão e o MIME type do arquivo, rejeitando arquivos inválidos com erro HTTP 400.

### RF02 - Autenticação e Autorização via JWT
- O endpoint de importação deve ser protegido por middleware/dependência de validação de token JWT (`Bearer Token`).
- Requisições sem token ou com token inválido/expirado devem ser rejeitadas com erro HTTP 401.

### RF03 - Motor de Extração Híbrido (pdfplumber + LLM Fallback)
- O sistema deve utilizar `pdfplumber` para extrair o texto do PDF página a página de forma performática.
- O pipeline deve identificar e extrair dados estruturados utilizando expressões regulares (Regex) e âncoras textuais baseadas no padrão SINACOR.
- Caso o PDF seja uma imagem escaneada ou possua layout fora do padrão, o sistema deve acionar um LLM (Ollama local ou Mistral API) via prompt estruturado e Pydantic para garantir a extração correta.

### RF04 - Extração do Cabeçalho da Nota
O parser deve identificar e extrair os seguintes campos essenciais:
- **Número da Nota:** Identificador único da nota de corretagem.
- **Data do Pregão:** Data de realização das operações (formato ISO `YYYY-MM-DD`).
- **Identificação do Cliente / CPF:** Para validação de titularidade.
- **Nome / Código da Corretora:** Identificação da instituição financeira.

### RF05 - Extração da Tabela de Negócios (Corpo da Nota)
Para cada linha de operação executada, o sistema deve extrair:
- **C/V:** Indicador de Compra (`C`) ou Venda (`V`).
- **Mercado:** Identificação do tipo de mercado (Vista, Fracionário, Futuro BM&F).
- **Especificação do Título / Ativo:** Ticker da ação (ex: `PETR4`) ou contrato futuro (ex: `WING26`, `WDOJ26`).
- **Quantidade:** Volume de títulos ou contratos negociados.
- **Preço / Ajuste:** Preço unitário da operação.
- **Valor Total:** Resultado da multiplicação Quantidade $\times$ Preço.
- **D/C:** Indicador de Débito (`D`) ou Crédito (`C`).

### RF06 - Extração do Resumo Financeiro e Custos (Rodapé)
O parser deve capturar com exatidão os custos operacionais e impostos da nota:
- **Taxa de Liquidação:** Cobrada pela clearing da B3.
- **Emolumentos:** Taxas da bolsa B3 sobre o volume financeiro.
- **Taxa de Corretagem:** Custo operacional cobrado pela corretora.
- **ISS:** Imposto municipal sobre a corretagem.
- **IRRF (Dedo-Duro):** Imposto de Renda Retido na Fonte (alíquota de 1% sobre o lucro bruto diário no Day Trade).
- **Valor Líquido da Nota:** Saldo final financeiro da nota.

### RF07 - Estruturação e Validação Pydantic
- Todos os dados extraídos devem ser validados e normalizados através de schemas rigorosos do Pydantic v2 antes de comporem a resposta HTTP.

---

## 5. Requisitos Não Funcionais (RNF)

### RNF01 - Performance e Tempo de Resposta
- O processamento síncrono no caminho feliz (Regex/pdfplumber) deve ser concluído em menos de 1.5 segundos por nota de até 3 páginas.
- O processamento via fallback LLM (Ollama/Mistral) deve ser otimizado para execução em até 10 segundos.

### RNF02 - Desacoplamento para Filas Futuras
- A arquitetura interna deve isolar o caso de uso de processamento (`NoteProcessorService`) da camada de transporte HTTP (`Rotas FastAPI`), permitindo que o mesmo serviço seja facilmente acoplado a um worker Celery ou ARQ no futuro sem reescrever a lógica de negócio.

### RNF03 - Conteinerização e Portabilidade (Docker)
- O sistema deve ser empacotado utilizando Docker (com `Dockerfile` otimizado multi-stage).
- Deve ser fornecido um arquivo `docker-compose.yml` contendo a declaração do serviço da API e as variáveis de ambiente para os ambientes de Desenvolvimento (`dev`) e Produção (`prod`).

### RNF04 - Segurança e Gestão de Segredos
- Nenhuma chave de API (Mistral, Ollama, JWT Secret) deve ser hardcodada. Todas devem ser injetadas exclusivamente via arquivo `.env`.
- O Swagger/OpenAPI deve refletir a necessidade de autenticação JWT (`HTTPBearer`).

---

## 6. Regras de Negócio e Conformidade Fiscal

### RN01 - Escopo Exclusivo Day Trade
Nesta primeira versão, o motor de extração e o contrato de dados focarão no processamento de notas contendo operações Day Trade (compra e venda do mesmo ativo, no mesmo dia, na mesma corretora).

### RN02 - Cálculo e Conversão de Mercado Futuro (BM&F)
Para minicontratos de índice (WIN) e dólar (WDO), o valor financeiro da nota reflete o ganho/perda de ajuste, e não o nocional do contrato.
- **Mini-índice (WIN):** Cada ponto equivale a R$ 0,20.
- **Mini-dólar (WDO):** Cada ponto equivale a R$ 10,00.
- O parser deve extrair corretamente o valor total do ajuste de posição gerado no pregão.

### RN03 - Dedutibilidade de Custos no Day Trade
Todas as taxas operacionais (emolumentos, liquidação, corretagem e ISS) reduzem o lucro tributável ou aumentam o prejuízo diário. O payload JSON retornado deve fornecer esses valores de forma segregada e clara para que o sistema cliente aplique o abatimento correto no fechamento mensal.

### RN04 - Rastreabilidade do IRRF (Dedo-Duro)
O valor do IRRF (1% sobre o lucro diário) deve ser retornado explicitamente no payload para permitir que o sistema cliente acumule esse crédito e o desconte do imposto total devido (20% sobre o lucro líquido mensal) no momento da geração do DARF (Código 6015).

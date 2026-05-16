# Product Requirements Document (PRD) - API de Importação de Notas de Corretagem (Day Trade & Swing Trade)

## 1. Visão Geral do Produto

O **Nota Corretagem API** é um microsserviço especializado, desenvolvido em Python (FastAPI), conteinerizado via Docker, com o objetivo de realizar a ingestão, extração e normalização de dados de notas de corretagem do mercado financeiro brasileiro (padrão SINACOR), cobrindo operações de **Day Trade** e **Swing Trade**.

A API atua como um motor de extração financeiro independente e desacoplado. Ela é consumida por outros sistemas do ecossistema via requisições HTTP REST autenticadas por tokens JWT. O sistema cliente envia o arquivo PDF da nota de corretagem (com suporte a envio de senha para PDFs protegidos), e a API devolve um payload JSON estruturado, contendo o cabeçalho da nota, a lista de operações (tabela de negócios com diferenciação clara entre Day Trade e Swing Trade) e o resumo financeiro detalhado (incluindo taxas, emolumentos e retenções de imposto como o IRRF "dedo-duro"). A persistência final desses dados no banco de dados relacional é responsabilidade exclusiva do sistema cliente.

---

## 2. Objetivos e Metas

- **Precisão Financeira Absoluta:** Garantir 100% de exatidão na extração de valores monetários, quantidades e identificação de débito/crédito (D/C).
- **Padronização SINACOR:** Suportar o padrão utilizado pela quase totalidade das corretoras brasileiras (XP, BTG, Clear, Rico, Genial, etc.).
- **Suporte a PDFs Protegidos por Senha:** Permitir que o sistema cliente envie a senha do PDF no payload da requisição para abertura e extração de notas criptografadas.
- **Suporte a Day Trade e Swing Trade:** Preparar o motor de extração e os contratos de dados para classificar e segregar operações iniciadas e encerradas no mesmo dia (Day Trade) daquelas mantidas em carteira (Swing Trade).
- **Arquitetura de Alta Performance e Desacoplada:** Utilizar FastAPI com processamento síncrono (Request $\rightarrow$ Response) otimizado, mantendo o design interno preparado para futura transição para processamento assíncrono baseado em filas (Celery/ARQ).
- **Segurança e Blindagem de Credenciais:** Proteger o acesso à API via autenticação JWT e isolar credenciais de IA (exclusivamente Mistral API) no arquivo `.env`.

---

## 3. Personas e Usuários

1. **Sistema Chamador (Backend Consumidor):** Aplicação principal do ecossistema que gerencia o usuário final, armazena o histórico no banco de dados e solicita o parse do PDF.
2. **Investidor / Trader (Usuário Final do Sistema Principal):** Realiza operações Day Trade e Swing Trade (Ações, Opções e Mercado Futuro BM&F) e necessita da importação automatizada de suas notas.
3. **Auditoria Fiscal (Receita Federal / Malha Fina):** Requer rastreabilidade completa entre o lucro bruto, as taxas operacionais dedutíveis, a segregação de alíquotas (20% Day Trade vs 15% Swing Trade) e o IRRF retido na fonte.

---

## 4. Requisitos Funcionais (RF)

### RF01 - Ingestão e Validação de Arquivo com Senha
- A API deve disponibilizar um endpoint `POST /api/v1/notas/importar` que aceite arquivos no formato PDF via `multipart/form-data`.
- O endpoint deve aceitar um campo opcional `password` (form data) contendo a senha para descriptografar PDFs protegidos.
- O sistema deve validar a extensão e o MIME type do arquivo, rejeitando arquivos inválidos com erro HTTP 400. Se a senha fornecida for incorreta para um PDF protegido, deve retornar erro HTTP 400 ou 422 com mensagem explicativa.

### RF02 - Autenticação e Autorização via JWT
- O endpoint de importação deve ser protegido por middleware/dependência de validação de token JWT (`Bearer Token`).
- Requisições sem token ou com token inválido/expirado devem ser rejeitadas com erro HTTP 401.

### RF03 - Motor de Extração Híbrido (pdfplumber + Mistral AI Fallback)
- O sistema deve utilizar `pdfplumber` para extrair o texto do PDF página a página de forma performática (passando o parâmetro `password` quando aplicável).
- O pipeline deve identificar e extrair dados estruturados utilizando expressões regulares (Regex) e âncoras textuais baseadas no padrão SINACOR.
- Caso o PDF seja uma imagem escaneada ou possua layout fora do padrão, o sistema deve acionar a API da **Mistral AI** em nuvem via prompt estruturado e Pydantic para garantir a extração correta.

### RF04 - Extração do Cabeçalho da Nota
O parser deve identificar e extrair os seguintes campos essenciais:
- **Número da Nota:** Identificador único da nota de corretagem.
- **Data do Pregão:** Data de realização das operações (formato ISO `YYYY-MM-DD`).
- **Identificação do Cliente / CPF:** Para validação de titularidade.
- **Nome / Código da Corretora:** Identificação da instituição financeira.

### RF05 - Extração da Tabela de Negócios (Corpo da Nota)
Para cada linha de operação executada, o sistema deve extrair:
- **C/V:** Indicador de Compra (`C`) ou Venda (`V`).
- **Mercado:** Identificação do tipo de mercado (Vista, Fracionário, Futuro BM&F, Opções).
- **Especificação do Título / Ativo:** Ticker da ação (ex: `PETR4`) ou contrato futuro (ex: `WING26`, `WDOJ26`).
- **Quantidade:** Volume de títulos ou contratos negociados.
- **Preço / Ajuste:** Preço unitário da operação.
- **Valor Total:** Resultado da multiplicação Quantidade $\times$ Preço.
- **D/C:** Indicador de Débito (`D`) ou Crédito (`C`).
- **Modalidade Operacional (Day Trade / Swing Trade):** Flag ou classificação indicando se a operação foi Day Trade (fechada no mesmo dia) ou Swing Trade.

### RF06 - Extração do Resumo Financeiro e Custos (Rodapé)
O parser deve capturar com exatidão os custos operacionais e impostos da nota:
- **Taxa de Liquidação:** Cobrada pela clearing da B3.
- **Emolumentos:** Taxas da bolsa B3 sobre o volume financeiro.
- **Taxa de Corretagem:** Custo operacional cobrado pela corretora.
- **ISS:** Imposto municipal sobre a corretagem.
- **IRRF (Dedo-Duro):** Imposto de Renda Retido na Fonte (alíquota de 1% sobre o lucro bruto diário no Day Trade, e 0,005% sobre o valor da venda no Swing Trade).
- **Valor Líquido da Nota:** Saldo final financeiro da nota.

### RF07 - Estruturação e Validação Pydantic
- Todos os dados extraídos devem ser validados e normalizados através de schemas rigorosos do Pydantic v2 antes de comporem a resposta HTTP.

---

## 5. Requisitos Não Funcionais (RNF)

### RNF01 - Performance e Tempo de Resposta
- O processamento síncrono no caminho feliz (Regex/pdfplumber) deve ser concluído em menos de 1.5 segundos por nota de até 3 páginas.
- O processamento via fallback Mistral API deve ser otimizado para execução em até 8 segundos.

### RNF02 - Desacoplamento para Filas Futuras
- A arquitetura interna deve isolar o caso de uso de processamento (`NoteProcessorService`) da camada de transporte HTTP (`Rotas FastAPI`), permitindo que o mesmo serviço seja facilmente acoplado a um worker Celery ou ARQ no futuro sem reescrever a lógica de negócio.

### RNF03 - Conteinerização e Portabilidade (Docker)
- O sistema deve ser empacotado utilizando Docker (com `Dockerfile` otimizado multi-stage).
- Deve ser fornecido um arquivo `docker-compose.yml` contendo a declaração do serviço da API e as variáveis de ambiente para os ambientes de Desenvolvimento (`dev`) e Produção (`prod`).

### RNF04 - Segurança e Gestão de Segredos
- Nenhuma chave de API (Mistral, JWT Secret) deve ser hardcodada. Todas devem ser injetadas exclusivamente via arquivo `.env`.
- O Swagger/OpenAPI deve refletir a necessidade de autenticação JWT (`HTTPBearer`).

---

## 6. Regras de Negócio e Conformidade Fiscal

### RN01 - Segregação de Operações (Day Trade vs. Swing Trade)
A Receita Federal proíbe misturar alíquotas e compensações:
- **Day Trade:** Alíquota de 20% sobre o lucro líquido. Não há isenção de R$ 20 mil. Prejuízo de Day Trade só compensa lucro de Day Trade.
- **Swing Trade:** Alíquota de 15% sobre o lucro líquido (com isenção para vendas de ações até R$ 20 mil no mês). Prejuízo de Swing Trade só compensa lucro de Swing Trade.
- O payload retornado pela API deve identificar claramente a modalidade de cada operação ou fornecer os dados atômicos necessários para que o algoritmo de match (casamento de ordens) do sistema cliente realize essa segregação.

### RN02 - Cálculo e Conversão de Mercado Futuro (BM&F)
Para minicontratos de índice (WIN) e dólar (WDO), o valor financeiro da nota reflete o ganho/perda de ajuste, e não o nocional do contrato.
- **Mini-índice (WIN):** Cada ponto equivale a R$ 0,20.
- **Mini-dólar (WDO):** Cada ponto equivale a R$ 10,00.
- O parser deve extrair corretamente o valor total do ajuste de posição gerado no pregão.

### RN03 - Dedutibilidade de Custos
Todas as taxas operacionais (emolumentos, liquidação, corretagem e ISS) reduzem o lucro tributável ou aumentam o prejuízo diário. O payload JSON retornado deve fornecer esses valores de forma segregada e clara para que o sistema cliente aplique o abatimento correto no fechamento mensal.

### RN04 - Rastreabilidade do IRRF (Dedo-Duro)
O valor do IRRF (1% para Day Trade e 0,005% para Swing Trade) deve ser retornado explicitamente no payload para permitir que o sistema cliente acumule esse crédito e o desconte do imposto total devido no momento da geração do DARF (Código 6015).

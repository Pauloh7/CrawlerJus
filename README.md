# CrawlerJus

API de consulta processual desenvolvida em Python para coleta estruturada de dados do **Tribunal de Justiça do Rio Grande do Sul (TJRS)**, com cache, tratamento de falhas, persistência de contexto e um agente de IA capaz de consultar e responder perguntas sobre processos judiciais.

O projeto nasceu a partir de um desafio técnico da **Jusbrasil** e evoluiu para um projeto de portfólio com foco em **web scraping resiliente, APIs assíncronas, observabilidade, testes, CI e aplicações de IA generativa**.

---

## Sumário

- [Visão geral](#visão-geral)
- [Principais funcionalidades](#principais-funcionalidades)
- [Arquitetura](#arquitetura)
- [Stack](#stack)
- [Como a coleta do TJRS funciona](#como-a-coleta-do-tjrs-funciona)
- [Agente de IA](#agente-de-ia)
- [Observabilidade](#observabilidade)
- [Executando o projeto](#executando-o-projeto)
- [API](#api)
- [Testes](#testes)
- [CI](#ci)
- [Tratamento de erros](#tratamento-de-erros)
- [Desafios técnicos](#desafios-técnicos)
- [Decisões de projeto](#decisões-de-projeto)
- [Limitações e próximos passos](#limitações-e-próximos-passos)
- [Autor](#autor)

---

## Visão geral

O CrawlerJus simula um cenário real de coleta de dados jurídicos em produção.

O sistema consulta processos do TJRS, normaliza e valida NPUs, reproduz o fluxo de autenticação utilizado pelo tribunal, trata falhas de comunicação, utiliza cache para reduzir acessos repetidos e entrega os dados através de uma API FastAPI.

Além da consulta tradicional, o projeto possui um agente baseado em **LangGraph + Ollama/Qwen**, capaz de decidir quando precisa consultar um processo e responder perguntas usando os dados processuais recuperados.

A aplicação foi estruturada para manter separadas as responsabilidades de:

- acesso ao tribunal;
- autenticação;
- parsing;
- regras de negócio;
- cache;
- API;
- agente de IA;
- persistência de contexto;
- observabilidade.

---

## Principais funcionalidades

### Coleta processual

- Consulta de processos do TJRS por NPU.
- Normalização e validação do número CNJ.
- Consulta de dados básicos, partes e movimentações.
- Requisições assíncronas e concorrentes.
- Autenticação dinâmica do TJRS reproduzida em Python.
- Renovação automática de credenciais.
- Retry com backoff para falhas transitórias.
- Tratamento específico para rate limit.
- Cache Redis com TTL configurável.
- Opção de ignorar o cache através de `force_refresh`.

### Agente de IA

- Orquestração com LangGraph.
- Modelo local Qwen executado através do Ollama.
- Tool calling para consulta processual.
- Reutilização de dados já consultados.
- Persistência de conversas e estado em PostgreSQL.
- Continuidade entre requisições utilizando `thread_id`.
- Contexto reduzido e direcionado para evitar enviar dados desnecessários ao modelo.
- Contadores de chamadas ao modelo, tools, consultas externas e reaproveitamento de dados.

### Engenharia e qualidade

- FastAPI.
- Docker e Docker Compose.
- PostgreSQL.
- Redis.
- Ruff.
- Pytest.
- Testes unitários e de integração.
- GitHub Actions.
- Logs estruturados em JSON.
- Request ID para rastreamento ponta a ponta.
- Execução do Ollama com aceleração NVIDIA quando disponível.

---

## Arquitetura

```text
                         ┌─────────────────────┐
                         │       Cliente       │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │       FastAPI       │
                         │                     │
                         │ /status             │
                         │ /search_npu         │
                         │ /ask_ia             │
                         └───────┬─────┬───────┘
                                 │     │
                    ┌────────────┘     └─────────────┐
                    ▼                                ▼
          ┌───────────────────┐             ┌──────────────────┐
          │   SearchService   │             │    LangGraph     │
          └─────────┬─────────┘             └────────┬─────────┘
                    │                                │
          ┌─────────┼─────────┐             ┌────────┼─────────┐
          ▼         ▼         ▼             ▼        ▼         ▼
       Redis      TJRS     Parsers        Qwen     Tools   PostgreSQL
        Cache    HTTP API               Ollama            Checkpoint
                    ▲                                │
                    └────────────────────────────────┘
                           consultar_processo
```

### Fluxo de consulta direta

```text
POST /search_npu
       │
       ▼
Validação e normalização do NPU
       │
       ▼
Consulta ao Redis
       │
       ├── HIT ──► resposta
       │
       └── MISS
              │
              ▼
        autenticação TJRS
              │
              ▼
   requisições assíncronas
              │
              ▼
            parsing
              │
              ▼
          cache Redis
              │
              ▼
           resposta
```

### Fluxo do agente

```text
POST /ask_ia
      │
      ▼
 carregar checkpoint
      │
      ▼
 preparar contexto
      │
      ▼
     Qwen
      │
      ├── consegue responder ─────────► resposta
      │
      └── precisa consultar processo
                    │
                    ▼
            consultar_processo
                    │
                    ▼
              SearchService
                    │
                    ▼
              atualizar estado
                    │
                    ▼
             preparar contexto
                    │
                    ▼
                  Qwen
                    │
                    ▼
                resposta
```

---

## Stack

| Área | Tecnologia |
|---|---|
| Linguagem | Python 3.12 |
| API | FastAPI |
| Servidor ASGI | Uvicorn |
| HTTP / scraping | `curl_cffi`, `httpx` |
| Parsing | BeautifulSoup |
| Assincronismo | `asyncio` |
| Retry | Tenacity |
| Cache | Redis |
| Agente | LangGraph |
| LLM | Qwen3 8B |
| Runtime LLM | Ollama |
| Checkpoint | PostgreSQL |
| Driver PostgreSQL | Psycopg |
| Containers | Docker / Docker Compose |
| Testes | Pytest |
| Lint | Ruff |
| CI | GitHub Actions |

---

## Como a coleta do TJRS funciona

O sistema de consulta processual do TJRS utiliza um fluxo de autenticação dinâmica antes de permitir o acesso aos dados.

De forma simplificada:

```text
1. Acessa a aplicação pública do TJRS
2. Obtém os dados necessários para autenticação
3. Resolve o challenge recebido pelo servidor
4. Reproduz o algoritmo esperado pelo TJRS
5. Obtém a autorização
6. Executa a consulta processual
7. Extrai e normaliza os dados
```

O challenge utiliza SHA-256 e dados fornecidos dinamicamente pelo servidor. Parte da lógica necessária para reproduzir o fluxo de autenticação foi identificada através de engenharia reversa do JavaScript da aplicação.

A implementação utiliza requisições HTTP, sem depender de Selenium ou Playwright para a coleta principal.

### Dados extraídos

Entre os dados retornados estão:

- número do processo;
- classe;
- assunto;
- natureza;
- comarca;
- órgão julgador;
- situação;
- partes;
- processos vinculados;
- movimentações processuais.

---

## Agente de IA

O endpoint `/ask_ia` disponibiliza uma camada conversacional sobre os dados processuais.

O agente utiliza um grafo com estado e pode decidir se precisa executar a tool `consultar_processo`.

### Componentes principais

```text
State
  │
  ├── messages
  ├── npu
  ├── process_data
  ├── context_data
  ├── llm_calls
  ├── tool_calls
  ├── external_calls
  └── cache_hits
```

O fluxo possui nós responsáveis por:

- preparar o contexto;
- chamar o modelo;
- executar a consulta processual quando necessário;
- reutilizar dados existentes;
- persistir o estado.

### Memória e checkpoint

O estado do LangGraph é persistido em PostgreSQL.

Isso permite continuar uma conversa utilizando o mesmo `thread_id`, inclusive após reinicializações da API.

Exemplo:

```text
Pergunta 1:
"Consulte o processo 5001646-66.2026.8.21.0008 e me diga a classe."

Pergunta 2:
"E quais são as partes dele?"
```

Na segunda pergunta, o agente pode reutilizar os dados processuais persistidos sem consultar novamente o tribunal.

---

## Observabilidade

Cada requisição HTTP recebe um `request_id` único.

Esse identificador acompanha a execução pelas diferentes camadas da aplicação:

```text
HTTP
 ↓
FastAPI
 ↓
LangGraph
 ↓
Tool
 ↓
SearchService
 ↓
TJRS
```

Os logs são estruturados em JSON e incluem informações como:

- `request_id`;
- endpoint;
- status HTTP;
- duração total;
- duração da chamada ao LLM;
- duração da consulta ao TJRS;
- cache hit/miss;
- número de tool calls;
- número de chamadas externas;
- tipo de erro.

Exemplo:

```json
{
  "timestamp": "2026-08-16T23:03:28.127795+00:00",
  "level": "INFO",
  "logger": "api.router",
  "event": "agent_request_completed",
  "request_id": "f80617af-66b6-4391-a0ac-21a44a31145f",
  "thread_id": "gpu-performance-test",
  "npu": "5001646-66.2026.8.21.0008",
  "duration_ms": 96254.89,
  "llm_calls": 2,
  "tool_calls": 1,
  "external_calls": 1,
  "cache_hits": 0,
  "error_type": null
}
```

O header `X-Request-ID` também é retornado ao cliente.

---

## Executando o projeto

### Pré-requisitos

- Docker
- Docker Compose
- Git

O `docker-compose.yml` atual está configurado para executar o Ollama com **GPU NVIDIA**. Para subir o ambiente exatamente como está versionado, também é necessário:

- GPU NVIDIA compatível;
- driver NVIDIA atualizado;
- suporte de GPU no Docker;
- no Windows, Docker Desktop utilizando backend WSL2.

Para desenvolvimento local sem Docker também é utilizado:

- Python 3.12
- Poetry

> O Ollama também suporta execução em CPU, mas o Compose atual reserva explicitamente uma GPU NVIDIA. Para executar o projeto sem GPU, remova o bloco de reserva de GPU do serviço `ollama` antes de subir o ambiente.

### Clonando o repositório

```bash
git clone git@github.com:Pauloh7/CrawlerJus.git
cd CrawlerJus
```

### Desenvolvimento com Docker

```bash
docker compose up -d
```

Verifique os serviços:

```bash
docker compose ps
```

Acompanhe os logs da API:

```bash
docker compose logs -f api
```

A API ficará disponível em:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

### Parando o ambiente

```bash
docker compose down
```

> Evite `docker compose down -v` se quiser preservar os volumes do PostgreSQL, Redis e Ollama.

### Produção

O projeto também possui um Compose dedicado ao ambiente de produção.

```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

---

## GPU para o Ollama

O `docker-compose.yml` atual reserva explicitamente uma **GPU NVIDIA** para o serviço `ollama`:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities:
            - gpu
```

Portanto, para executar o ambiente de desenvolvimento **sem alterações no Compose**, o Docker precisa conseguir acessar uma GPU NVIDIA.

No Windows, isso normalmente envolve:

- driver NVIDIA atualizado;
- WSL2 atualizado;
- Docker Desktop utilizando o backend WSL2;
- suporte de GPU habilitado no Docker.

Uma forma de validar o acesso à GPU pelo Docker é:

```bash
docker run --rm --gpus all ubuntu nvidia-smi
```

Depois que o Ollama estiver carregando o modelo, é possível verificar o backend utilizado com:

```bash
docker compose exec ollama ollama ps
```

Exemplo com aceleração por GPU:

```text
NAME        SIZE      PROCESSOR
qwen3:8b    5.6 GB    100% GPU
```

### Execução sem GPU

O Ollama suporta execução em CPU, mas o Compose versionado neste projeto **não está configurado como CPU-only**.

Para executar sem GPU NVIDIA, remova do serviço `ollama` o bloco:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all
          capabilities:
            - gpu
```

Depois disso, o Ollama poderá iniciar utilizando CPU, com latência de inferência significativamente maior.

> A configuração de GPU não é necessária para o crawler do TJRS, Redis, PostgreSQL ou FastAPI. Ela é utilizada apenas para acelerar o modelo local executado pelo Ollama.

---

# API

## `GET /status`

Verifica a disponibilidade da API e da fonte externa.

### Exemplo

```bash
curl "http://localhost:8000/status"
```

### Resposta

```json
{
  "status": "ok",
  "api": "ok",
  "tribunal_site": "ok",
  "response_time_ms": 812.19
}
```

---

## `POST /search_npu`

Consulta diretamente um processo.

### Body

```json
{
  "npu": "5001646-66.2026.8.21.0008"
}
```

### Parâmetros

| Parâmetro | Tipo | Descrição |
|---|---|---|
| `npu` | string | Número CNJ do processo |
| `force_refresh` | boolean | Ignora o cache e força nova consulta |

### Exemplo

```bash
curl -X POST   "http://localhost:8000/search_npu?force_refresh=false"   -H "Content-Type: application/json"   -d '{
    "npu": "5001646-66.2026.8.21.0008"
  }'
```

### Exemplo de resposta

```json
{
  "numeroProcesso": "5001646-66.2026.8.21.0008",
  "numeroProcessoCNJ": "50016466620268210008",
  "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
  "nomeClasse": "CUMPRIMENTO DE SENTENÇA",
  "comarca": "CANOAS",
  "codigoComarca": "8",
  "partes": [
    {
      "descricaoTipo": "EXEQUENTE",
      "nome": "..."
    },
    {
      "descricaoTipo": "EXECUTADO",
      "nome": "..."
    }
  ],
  "movimentos": [
    {
      "data": "15/01/2026",
      "descricao": "Conclusos para decisão"
    }
  ]
}
```

---

## `POST /ask_ia`

Permite fazer perguntas em linguagem natural sobre um processo.

### Body

```json
{
  "thread_id": "processo-5001646",
  "question": "Consulte o processo 5001646-66.2026.8.21.0008 e me diga qual é a classe."
}
```

### Exemplo

```bash
curl -X POST   "http://localhost:8000/ask_ia"   -H "Content-Type: application/json"   -d '{
    "thread_id": "processo-5001646",
    "question": "Consulte o processo 5001646-66.2026.8.21.0008 e me diga qual é a classe."
  }'
```

### Exemplo de resposta

```json
{
  "answer": "O processo está classificado como Cumprimento de Sentença.",
  "thread_id": "processo-5001646",
  "npu": "5001646-66.2026.8.21.0008",
  "llm_calls": 2,
  "tool_calls": 1,
  "external_calls": 1,
  "cache_hits": 0,
  "error": null,
  "error_type": null
}
```

### Continuidade da conversa

Utilizando o mesmo `thread_id`:

```json
{
  "thread_id": "processo-5001646",
  "question": "E quais são as partes dele?"
}
```

O estado anterior é recuperado do PostgreSQL e pode ser reutilizado pelo agente.

---

## Cache

A consulta processual utiliza Redis.

```text
NPU
 │
 ▼
Redis
 │
 ├── HIT  → retorna imediatamente
 │
 └── MISS → consulta TJRS
                 │
                 ▼
               Redis
```

O TTL pode ser configurado através de:

```text
CACHE_TTL_SECONDS
```

---

## Tratamento de erros

A aplicação possui exceções específicas para diferenciar problemas de entrada, autenticação, rate limit, upstream e parsing.

| Situação | Comportamento |
|---|---|
| NPU inválido | erro de validação |
| Processo inexistente | erro específico de processo não encontrado |
| 401 / 403 | renovação/reprocessamento da autenticação |
| HTTP 429 | retry com backoff |
| HTTP 5xx | erro de upstream |
| HTML inesperado | erro de upstream |
| JSON inválido | erro de parsing |
| Falha inesperada | HTTP 500 genérico com `request_id` |

As respostas de erro incluem `request_id`, facilitando a correlação com os logs.

---

# Testes

## Unitários

```bash
poetry run pytest tests/unit -q
```

Estado atual:

```text
41 passed
```

Os testes cobrem, entre outros pontos:

- validação e utilitários de NPU;
- extractors;
- SearchService;
- seleção de NPU pelo agente;
- preparação de contexto;
- routing do LangGraph;
- tool calling;
- reutilização de dados;
- comportamento da API;
- Request ID.

## Integração

Checkpoint PostgreSQL:

```bash
poetry run pytest tests/integration/test_checkpoint_postgres.py -q
```

Estado atual:

```text
3 passed
```

## Lint

```bash
poetry run ruff check .
```

## Validação Poetry

```bash
poetry check
```

## Build

```bash
poetry build
```

---

# CI

O projeto possui pipeline no GitHub Actions executado em `push` e `pull_request`.

### Unit tests

```text
poetry check
      ↓
poetry install
      ↓
ruff check .
      ↓
pytest tests/unit
      ↓
poetry build
```

### Integração

O GitHub Actions inicia um PostgreSQL temporário e executa:

```text
pytest tests/integration/test_checkpoint_postgres.py
```

Os testes de avaliação do agente que dependem de modelo e serviços externos ficam fora do pipeline principal para evitar tornar o CI lento e instável.

---

# Desafios técnicos

## Autenticação dinâmica do TJRS

O maior desafio da coleta foi reproduzir o fluxo de autenticação utilizado pelo TJRS.

O tribunal disponibiliza um challenge que precisa ser resolvido antes da consulta. O processo exige reproduzir parte da lógica encontrada no JavaScript da aplicação e gerar corretamente os dados esperados pelo backend.

Como os valores utilizados pelo site podem mudar, a solução evita depender apenas de constantes fixas.

## Rate limiting

O TJRS pode responder com HTTP `429`.

Para evitar que esse comportamento torne a aplicação instável foram implementados:

- retry;
- backoff;
- tratamento de `Retry-After`;
- cache;
- exceções específicas.

## Mudanças na fonte

Sites públicos mudam HTML, JavaScript e regras de acesso com frequência.

Por isso a aplicação mantém separadas as responsabilidades de HTTP, autenticação, parsing, serviço e API.

## Agente com estado persistente

O uso do PostgreSQL como checkpointer do LangGraph permite restaurar o estado utilizando um `thread_id`, sem depender apenas da memória do processo Python.

## Observabilidade ponta a ponta

Uma requisição do agente pode atravessar várias camadas e serviços externos. O Request ID permite correlacionar o fluxo e medir quanto tempo foi gasto em LLM, TJRS, cache, tools e na requisição completa.

---

# Decisões de projeto

### Por que HTTP em vez de Selenium?

A coleta principal foi construída utilizando requisições HTTP para manter o crawler mais leve, previsível e eficiente.

### Por que Redis?

Evita consultas repetidas ao tribunal e reduz a chance de rate limit.

### Por que PostgreSQL?

É utilizado como backend persistente para os checkpoints do LangGraph.

### Por que Ollama?

Permite executar o modelo localmente, sem depender de uma API externa de LLM.

### Por que LangGraph?

O agente precisa manter estado, executar tools, decidir quando consultar dados e continuar a conversa.

---

# Limitações e próximos passos

O projeto atualmente é voltado para estudo e portfólio e não foi desenhado para exposição irrestrita na internet.

Possíveis evoluções:

- otimizar a latência do modelo local;
- avaliar modelos menores para decisões simples de tool calling;
- melhorar métricas de tokens e tempo de inferência;
- adicionar métricas agregadas de cache e erros;
- adicionar lock distribuído para regeneração de autenticação;
- ampliar cenários de testes de falha;
- tornar a extração de dados do JavaScript ainda menos dependente de regex;
- expandir a arquitetura para outros tribunais;
- adicionar autenticação e rate limiting caso a API seja publicada.

---

# Estrutura geral do projeto

```text
CrawlerJus/
├── api/
│   ├── router.py
│   ├── error_handlers.py
│   ├── logging_config.py
│   └── request_context.py
│
├── crawler_jus/
│   ├── services/
│   │   └── search_service.py
│   └── ...
│
├── legal_ai/
│   ├── nodes.py
│   ├── tools.py
│   └── ...
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── ...
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
├── pyproject.toml
└── README.md
```

---

# Autor

**Paulo Henrique De Souza Gomes**

[LinkedIn](https://www.linkedin.com/in/paulo-henrique-4a849139/)

---

## Observação

Este projeto realiza consultas sobre uma fonte pública e foi desenvolvido com finalidade de estudo, demonstração técnica e portfólio.

A disponibilidade e a estrutura dos dados dependem do serviço externo consultado. Mudanças no TJRS podem exigir adaptações na camada de coleta.

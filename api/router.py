import logging
import os
import time
from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from api import schema
from api.enums import HealthStatus
from api.error_handlers import generic_exception_handler, tjrs_exception_handler
from api.exceptions import TJRSBaseError
from api.logging_config import configure_logging
from api.request_context import RequestContextMiddleware, request_id_context
from crawler_jus.crawler import Crawler
from crawler_jus.services.search_service import SearchService
from legal_ai.graph import create_legal_graph

load_dotenv()
configure_logging()

logger = logging.getLogger(__name__)

TJRS_URL = "https://www.tjrs.jus.br/novo/busca/?return=proc&client=wp_index#"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia os recursos compartilhados durante o ciclo de vida da API.
    
    Inicializa crawler, SearchService, checkpoint PostgreSQL e grafo jurídico, armazenando-os em app.state e fechando o crawler no shutdown.
    
    Args:
        app (FastAPI): Instância da aplicação FastAPI.
    """
    crawler = Crawler()
    service = SearchService(crawler)
    db_url = os.getenv("LANGGRAPH_DB_URL")

    if not db_url:
        raise RuntimeError("LANGGRAPH_DB_URL não configurada.")

    try:
        async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:
            await checkpointer.setup()

            legal_graph = create_legal_graph(
                service,
                checkpointer,
            )

            app.state.crawler = crawler
            app.state.search_service = service
            app.state.legal_graph = legal_graph
            yield

    finally:
        await crawler.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(RequestContextMiddleware)

app.add_exception_handler(
    TJRSBaseError,
    tjrs_exception_handler,
)

app.add_exception_handler(
    Exception,
    generic_exception_handler,
)

@app.get("/status")
async def healthcheck():
    """Verifica a disponibilidade da API e do site do TJRS.
    
    Returns:
        dict: Status geral, status da API, status do tribunal e tempo de resposta do site em milissegundos.
    """
    api_status = HealthStatus.OK
    site_status = HealthStatus.DOWN
    response_time_ms = None

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(TJRS_URL)

        elapsed = (time.time() - start) * 1000
        response_time_ms = round(elapsed, 2)

        if resp.status_code < 500:
            site_status = HealthStatus.OK
    except Exception:
        site_status = HealthStatus.DOWN

    overall_status = (
        HealthStatus.OK if site_status == HealthStatus.OK else HealthStatus.DEGRADED
    )

    return {
        "status": overall_status,
        "api": api_status,
        "tribunal_site": site_status,
        "response_time_ms": response_time_ms,
    }


@app.post("/search_npu")
async def search_npu(
    cliente: schema.ClienteInput,
    force_refresh: bool = Query(False),
) -> dict:
    """
    Recebe um NPU e executa a consulta dos dados do processo.

    Args:
        cliente: Payload contendo o número do processo.
        force_refresh: Se True, ignora o cache Redis.

    Returns:
        Dicionário com os dados do processo.
    """
    return await app.state.search_service.search_npu(
        cliente.npu,
        force_refresh=force_refresh,
    )


@app.post(
    "/ask_ia",
    response_model=schema.AskIAResponse,
)
@app.post(
    "/ask_ia",
    response_model=schema.AskIAResponse,
)
async def ask_ia(
    data: schema.AskIAInput,
):
    """Executa uma pergunta no grafo jurídico mantendo o contexto da thread.

    Args:
        data (schema.AskIAInput): Identificador da thread e pergunta do usuário.

    Returns:
        dict: Resposta do agente, NPU atual, contadores de execução
        e dados de erro.
    """
    request_id = request_id_context.get()
    started_at = time.perf_counter()

    graph = app.state.legal_graph

    config = {
        "configurable": {
            "thread_id": data.thread_id,
        }
    }

    logger.info(
        "agent_request_started",
        extra={
            "request_id": request_id,
            "thread_id": data.thread_id,
        },
    )

    result = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": data.question,
                }
            ]
        },
        config=config,
    )

    answer = result["messages"][-1].content

    duration_ms = (
        time.perf_counter() - started_at
    ) * 1000

    logger.info(
        "agent_request_completed",
        extra={
            "request_id": request_id,
            "thread_id": data.thread_id,
            "npu": result.get("npu"),
            "duration_ms": round(duration_ms, 2),
            "llm_calls": result.get("llm_calls", 0),
            "tool_calls": result.get(
                "tool_calls_count",
                0,
            ),
            "external_calls": result.get(
                "external_calls_count",
                0,
            ),
            "cache_hits": result.get(
                "cache_hits",
                0,
            ),
            "error_type": result.get("error_type"),
        },
    )

    return {
        "answer": answer,
        "thread_id": data.thread_id,
        "npu": result.get("npu"),
        "llm_calls": result.get("llm_calls"),
        "tool_calls": result.get(
            "tool_calls_count"
        ),
        "external_calls": result.get(
            "external_calls_count"
        ),
        "cache_hits": result.get("cache_hits"),
        "error": result.get("error"),
        "error_type": result.get("error_type"),
    }
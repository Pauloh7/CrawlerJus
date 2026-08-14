import time
import httpx
from . import schema
from fastapi import Query
from contextlib import asynccontextmanager
from fastapi import FastAPI
from crawler_jus.crawler import Crawler
from crawler_jus.services.search_service import SearchService
from api.exceptions import TJRSBaseError
from api.error_handlers import tjrs_exception_handler, generic_exception_handler
from api.enums import HealthStatus
from legal_ai.agent import create_legal_agent
from legal_ai.graph import create_legal_graph

@asynccontextmanager
async def lifespan(app: FastAPI):
    crawler = Crawler()
    service = SearchService(crawler)

    legal_graph = create_legal_graph(service)

    app.state.crawler = crawler
    app.state.search_service = service
    app.state.legal_graph = legal_graph

    try:
        yield

    finally:
        await crawler.close()


app = FastAPI(lifespan=lifespan)

app.add_exception_handler(TJRSBaseError, tjrs_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

TJRS_URL = "https://www.tjrs.jus.br/novo/busca/?return=proc&client=wp_index#"

@app.get("/status")


@app.get("/status")
async def healthcheck():
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
async def search_npu(cliente: schema.ClienteInput, force_refresh: bool = Query(False)) -> dict:
    """Parte da api que recebe o post com dados do processo e executa chamada para extração dos dados
    Args:
        cliente (schema.ClienteInput): Json com numero do processo
        force_refresh (bool): Determina se é para forçar ou nao refresh no cache redis
    Returns:
        processo_info (dict): Dicionário com dados do processo
    """
    return await app.state.search_service.search_npu(cliente.npu, force_refresh=force_refresh)

@app.post(
    "/ask_ia",
    response_model=schema.AskIAResponse,
)
async def ask_ia(
    data: schema.AskIAInput,
):
    graph = app.state.legal_graph

    config = {
        "configurable": {
            "thread_id": data.thread_id
        }
    }

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

    return {
    "answer": answer,
    "thread_id": data.thread_id,

    "npu": result.get("npu"),

    "llm_calls": result.get(
        "llm_calls"
    ),

    "tool_calls": result.get(
        "tool_calls_count"
    ),

    "external_calls": result.get(
        "external_calls_count"
    ),

    "cache_hits": result.get(
        "cache_hits"
    ),
    }
    

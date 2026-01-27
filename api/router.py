import time
import httpx
from . import schema
from fastapi import Query
from contextlib import asynccontextmanager
from fastapi import FastAPI
from crawler_jus.crawler import Crawler
from crawler_jus.services.search_service import SearchService
from .error_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    crawler = Crawler()
    app.state.crawler = crawler

    yield

    await crawler.close()


app = FastAPI(lifespan=lifespan)

register_exception_handlers(app)

TJRS_URL = "https://www.tjrs.jus.br/novo/busca/?return=proc&client=wp_index#"

@app.get("/status")
async def healthcheck():
    api_status = "ok"
    site_status = "down"
    response_time_ms = None

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(TJRS_URL)
        elapsed = (time.time() - start) * 1000
        response_time_ms = round(elapsed, 2)

        if resp.status_code < 500:
            site_status = "ok"
    except Exception:
        site_status = "down"

    overall_status = "ok" if site_status == "ok" else "degraded"

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
    service = SearchService(app.state.crawler)
    return await service.search_npu(cliente.npu, force_refresh=force_refresh)
    

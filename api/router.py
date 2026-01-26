from . import schema
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from crawler_jus.crawler import Crawler
from fastapi.responses import JSONResponse
from crawler_jus.exceptions import TJRSRateLimit,TJRSBadResponse
from crawler_jus.services.search_service import SearchService



@asynccontextmanager
async def lifespan(app: FastAPI):
    crawler = Crawler()
    app.state.crawler = crawler

    yield

    await crawler.close()


app = FastAPI(lifespan=lifespan)


@app.post("/search_npu")
async def search_npu(cliente: schema.ClienteInput) -> dict:
    """Parte da api que recebe o post com dados do processo e executa chamada para extração dos dados
    Args:
        cliente (schema.ClienteInput): Json com numero do processo
    Returns:
        processo_info (dict): Dicionário com dados do processo
    Raises:
        HTTPException: Erro de processamento na requisição
        TJRSRateLimit: Erro de limite de requisiçoes
    """
    service = SearchService(app.state.crawler)
    try:
        return await service.search_npu(cliente.npu)
    except TJRSRateLimit as e:
        return JSONResponse(
            status_code=429,
            content={"detail": e.message},
            headers={"Retry-After": str(e.retry_after)},
        )
    except TJRSBadResponse as e:
        raise HTTPException(
            status_code=502,
            detail=e.message,
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao processar a requisição.")

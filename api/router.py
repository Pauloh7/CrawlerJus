import asyncio
from . import schema
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from crawler_jus.crawler import Crawler
from crawler_jus.util import *
from fastapi.responses import JSONResponse
from crawler_jus.exceptions import TJRSRateLimit
from api.cache import get_cache, set_cache



@asynccontextmanager
async def lifespan(app: FastAPI):
    crawler = Crawler()
    app.state.crawler = crawler

    yield

    await crawler.close()


app = FastAPI(lifespan=lifespan)

@app.post("/search_npu/")
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

    try:
        crawler: Crawler = app.state.crawler
        npu = remove_special_characters(cliente.npu)
        comarca = extract_comarca(npu)
        cache_key = f"tjrs:{comarca}:{npu}"
        cached = await get_cache(cache_key)
        if cached:
            return cached
        urlconsult = build_url_processo(npu,comarca)
        urlmovimentos = build_url_movimento(npu,comarca)
        if not valida_npu(npu):
            raise HTTPException(
                status_code=400,
                detail="Número do processo inválido",
            )
        
        basic_data_json, movimentos_json = await asyncio.gather(
            crawler.request_page(urlconsult),
            crawler.request_page(urlmovimentos),
        )
        basic_data = crawler.extract_basic_data_partes(basic_data_json)
        movimentos = crawler.extract_movimentos(movimentos_json)

        results = {**basic_data, "movimentos": movimentos}
        

        if not results:
            raise HTTPException(
                status_code=404, detail="Nenhum processo encontrado"
            )
        
        await set_cache(cache_key, results)

        return results
    except TJRSRateLimit as e:
        return JSONResponse(
            status_code=429,
            content={"detail": e.message},
            headers={"Retry-After": str(e.retry_after)},
        )
    
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao processar a requisição.")

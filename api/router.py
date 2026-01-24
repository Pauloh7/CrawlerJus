import asyncio
from . import schema
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from crawler_jus.crawler import Crawler
from crawler_jus.util import *


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
    """

    try:
        crawler: Crawler = app.state.crawler
        npu = remove_special_characters(cliente.npu)
        comarca = extract_comarca(npu)
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

        return results

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao processar a requisição.")

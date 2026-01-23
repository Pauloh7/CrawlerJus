import asyncio
import json
import schema
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from crawler_jus.crawler import Crawler
from crawler_jus.util import *


@asynccontextmanager
async def lifespan(app: FastAPI):
    crawler = Crawler()
    app.state.crawler = crawler

    yield

    await crawler.aclose()


app = FastAPI(lifespan=lifespan)

@app.post("/search_npu/")
async def search_npu(cliente: schema.ClienteInput) -> list[dict]:
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
        urlconsult = f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaProcesso?numeroProcesso={npu}&codComarca={comarca}"
        urlmovimentos = f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaMovimentacao?numeroProcesso=50016466620268210008&codComarca=8"
        urlmovimentos = f""
        if not valida_npu(npu):
            raise HTTPException(
                status_code=400,
                detail="Número do processo inválido",
            )
        auth = request_auth()
        page_basic_data, page_partes,page_movimentos = await asyncio.gather(
            crawler.send_request(auth,urlconsult),
            crawler.send_request(auth,urlmovimentos),
        )
        results = {
            **extract_basic_data(basic_data_json),
            **extract_movimentos(movimentos_json),
        }

        results
        if not results:
            raise HTTPException(
                status_code=404, detail="Nenhum processo encontrado"
            )

        return results

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Erro ao processar a requisição.")

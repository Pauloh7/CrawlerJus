import asyncio
from fastapi import HTTPException

from crawler_jus.cache import get_cache, set_cache
from crawler_jus.crawler import Crawler
from api.exceptions import TJRSUnauthorized, TJRSRateLimit, TJRSUpstreamError, TJRSNetworkError
from crawler_jus.util import (
    remove_special_characters,
    valida_npu,
    extract_comarca,
    build_url_processo,
    build_url_movimento,
)


class SearchService:
    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    async def search_npu(self, npu_original: str) -> dict:
        """Seviço que serve com as regras de negocio a rota de search_npu
        Args:
            npu_original (str): npu enviado para busca
        Returns:
            results (dict): Dicionário com dados do processo
        Raises:
            TJRSRateLimit: Erro de limite de requisiçoes
        """
        # 1) normaliza e valida
        npu = remove_special_characters(npu_original)
        if not valida_npu(npu):
            raise HTTPException(status_code=400, detail="Número do processo inválido")

        # 2) prepara contexto
        comarca = extract_comarca(npu)
        cache_key = f"tjrs:{comarca}:{npu}"

        # 3) tenta buscar na cache
        try:
            cached = await get_cache(cache_key)
        except Exception:
            cached = None

        if cached:
            return cached
        
        urlconsult = build_url_processo(npu, comarca)
        urlmovimentos = build_url_movimento(npu, comarca)
        
        # 4) fetch concorrente com tratamento estável
        basic_data_json, movimentos_json = await asyncio.gather(
            self.crawler.request_page(urlconsult),
            self.crawler.request_page(urlmovimentos),
            return_exceptions=True,
        )
        
        for response in (basic_data_json, movimentos_json):
            if isinstance(response, HTTPException):
                raise response
            if isinstance(response, (TJRSUnauthorized, TJRSRateLimit, TJRSUpstreamError, TJRSNetworkError)):
                raise response
            if isinstance(response, Exception):
                raise HTTPException(status_code=500, detail=f"Erro inesperado: {type(response).__name__}")
        

        # 5) parse e montagem
        try:
            basic_data = self.crawler.extract_basic_data_partes(basic_data_json)
            movimentos = self.crawler.extract_movimentos(movimentos_json)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Falha ao processar resposta do TJRS: {type(e).__name__}")
        
        results = {**basic_data, "movimentos": movimentos}

        if not results:
            raise HTTPException(status_code=404, detail="Nenhum processo encontrado")

        # 6) seta resultado na cache
        try:
            await set_cache(cache_key, results)
        except Exception:
            pass

        return results
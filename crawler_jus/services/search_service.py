import asyncio
import logging

from api.exceptions import (
    ProcessNotFoundError,
    TJRSNetworkError,
    TJRSParseError,
    TJRSRateLimit,
    TJRSUnauthorized,
    TJRSUpstreamError,
)
from crawler_jus.cache import (
    get_cache,
    set_cache,
)
from crawler_jus.crawler import Crawler
from crawler_jus.util import (
    build_url_movimento,
    build_url_processo,
    extract_comarca,
    normalize_npu_to_20_digits,
)

logger = logging.getLogger(__name__)


class SearchService:
    """Serviço responsável por orquestrar a consulta de processos no TJRS.
    
    Centraliza normalização do NPU, cache, chamadas concorrentes ao crawler, parsing e tratamento de erros da consulta.
    """
    def __init__(
        self,
        crawler: Crawler,
    ):
        """Inicializa o serviço com o crawler usado para acessar o TJRS.
        
        Args:
            crawler (Crawler): Instância responsável pelas requisições e extração dos dados.
        """
        self.crawler = crawler

    async def search_npu(
        self,
        npu_original: str,
        force_refresh: bool = False,
    ) -> dict:
        """
        Serviço responsável pelas regras de negócio
        da consulta de processos no TJRS.

        Args:
            npu_original:
                Número do processo informado pelo usuário.

            force_refresh:
                Se True, ignora o cache e força
                nova consulta ao TJRS.

        Returns:
            Dicionário com os dados do processo.

        Raises:
            ValueError:
                Quando o NPU informado não pode ser normalizado.

            TJRSUnauthorized:
                Falha de autenticação no TJRS.

            TJRSRateLimit:
                Limite de requisições do TJRS.

            TJRSUpstreamError:
                Erro inesperado retornado pelo serviço do TJRS.

            TJRSNetworkError:
                Falha de rede durante a consulta.

            TJRSParseError:
                Falha ao interpretar a resposta do TJRS.

            ProcessNotFoundError:
                Processo não encontrado ou sem dados.
        """

        # 1. Normalização
        npu_digits20 = normalize_npu_to_20_digits(npu_original)

        comarca = extract_comarca(npu_digits20)

        cache_key = f"tjrs:{comarca}:{npu_digits20}"

        # 2. Consulta ao cache
        if not force_refresh:
            try:
                cached = await get_cache(cache_key)

                if cached:
                    return cached

            except Exception:
                logger.exception(
                    "Falha ao consultar cache Redis",
                    extra={
                        "cache_key": cache_key,
                        "npu": npu_digits20,
                    },
                )

        # 3. Montagem das URLs
        url_consulta = build_url_processo(
            npu_digits20,
            comarca,
        )

        url_movimentos = build_url_movimento(
            npu_digits20,
            comarca,
        )

        # 4. Requisições concorrentes
        basic_data_response, movimentos_response = await asyncio.gather(
            self.crawler.request_page(url_consulta),
            self.crawler.request_page(url_movimentos),
            return_exceptions=True,
        )

        # 5. Propagação de erros conhecidos
        for response in (
            basic_data_response,
            movimentos_response,
        ):
            if isinstance(
                response,
                (
                    TJRSUnauthorized,
                    TJRSRateLimit,
                    TJRSUpstreamError,
                    TJRSNetworkError,
                ),
            ):
                raise response

            if isinstance(
                response,
                Exception,
            ):
                raise TJRSUpstreamError(
                    "Erro inesperado durante "
                    "a consulta ao TJRS: "
                    f"{type(response).__name__}"
                )

        # 6. Parsing da resposta
        try:
            basic_data = self.crawler.extract_basic_data_partes(basic_data_response)

            movimentos = self.crawler.extract_movimentos(movimentos_response)

        except Exception as exc:
            raise TJRSParseError(
                f"Falha ao processar a resposta do TJRS: {type(exc).__name__}"
            ) from exc

        # 7. Verifica se o processo existe
        if not basic_data:
            raise ProcessNotFoundError(
                "TJRS não retornou dados para o processo informado."
            )

        # 8. Montagem do resultado
        results = {
            **basic_data,
            "movimentos": movimentos,
        }

        # 9. Escrita no cache
        try:
            await set_cache(
                cache_key,
                results,
                ttl=60,
            )

        except Exception:
            logger.exception(
                "Falha ao gravar cache Redis",
                extra={
                    "cache_key": cache_key,
                    "npu": npu_digits20,
                },
            )

        return results

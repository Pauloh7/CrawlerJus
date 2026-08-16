import asyncio
import logging
import time

from api.exceptions import (
    ProcessNotFoundError,
    TJRSNetworkError,
    TJRSParseError,
    TJRSRateLimit,
    TJRSUnauthorized,
    TJRSUpstreamError,
)
from api.request_context import request_id_context
from crawler_jus.cache import get_cache, set_cache
from crawler_jus.crawler import Crawler
from crawler_jus.util import (
    build_url_movimento,
    build_url_processo,
    extract_comarca,
    normalize_npu_to_20_digits,
)

logger = logging.getLogger(__name__)


class SearchService:
    """Orquestra consultas processuais ao TJRS."""

    def __init__(
        self,
        crawler: Crawler,
    ):
        self.crawler = crawler

    async def search_npu(
        self,
        npu_original: str,
        force_refresh: bool = False,
    ) -> dict:
        """Consulta um processo no TJRS com cache e tratamento de falhas."""

        started_at = time.perf_counter()

        request_id = request_id_context.get()

        npu_digits20 = normalize_npu_to_20_digits(
            npu_original
        )

        comarca = extract_comarca(npu_digits20)

        cache_key = (
            f"tjrs:{comarca}:{npu_digits20}"
        )

        logger.info(
            "process_search_started",
            extra={
                "request_id": request_id,
                "npu": npu_digits20,
                "comarca": comarca,
                "force_refresh": force_refresh,
            },
        )

        # --------------------------------------------------
        # CACHE
        # --------------------------------------------------

        if not force_refresh:
            cache_started_at = time.perf_counter()

            try:
                cached = await get_cache(cache_key)

                cache_duration_ms = (
                    time.perf_counter()
                    - cache_started_at
                ) * 1000

                if cached:
                    logger.info(
                        "process_cache_hit",
                        extra={
                            "request_id": request_id,
                            "npu": npu_digits20,
                            "cache_key": cache_key,
                            "duration_ms": round(
                                cache_duration_ms,
                                2,
                            ),
                        },
                    )

                    total_duration_ms = (
                        time.perf_counter()
                        - started_at
                    ) * 1000

                    logger.info(
                        "process_search_completed",
                        extra={
                            "request_id": request_id,
                            "npu": npu_digits20,
                            "source": "cache",
                            "duration_ms": round(
                                total_duration_ms,
                                2,
                            ),
                        },
                    )

                    return cached

                logger.info(
                    "process_cache_miss",
                    extra={
                        "request_id": request_id,
                        "npu": npu_digits20,
                        "cache_key": cache_key,
                        "duration_ms": round(
                            cache_duration_ms,
                            2,
                        ),
                    },
                )

            except Exception:
                logger.exception(
                    "process_cache_read_failed",
                    extra={
                        "request_id": request_id,
                        "cache_key": cache_key,
                        "npu": npu_digits20,
                    },
                )

        else:
            logger.info(
                "process_cache_bypassed",
                extra={
                    "request_id": request_id,
                    "npu": npu_digits20,
                },
            )

        # --------------------------------------------------
        # URLs
        # --------------------------------------------------

        url_consulta = build_url_processo(
            npu_digits20,
            comarca,
        )

        url_movimentos = build_url_movimento(
            npu_digits20,
            comarca,
        )

        # --------------------------------------------------
        # TJRS
        # --------------------------------------------------

        upstream_started_at = time.perf_counter()

        logger.info(
            "tjrs_requests_started",
            extra={
                "request_id": request_id,
                "npu": npu_digits20,
            },
        )

        basic_data_response, movimentos_response = (
            await asyncio.gather(
                self.crawler.request_page(
                    url_consulta
                ),
                self.crawler.request_page(
                    url_movimentos
                ),
                return_exceptions=True,
            )
        )

        upstream_duration_ms = (
            time.perf_counter()
            - upstream_started_at
        ) * 1000

        logger.info(
            "tjrs_requests_completed",
            extra={
                "request_id": request_id,
                "npu": npu_digits20,
                "duration_ms": round(
                    upstream_duration_ms,
                    2,
                ),
            },
        )

        # --------------------------------------------------
        # ERROS DO UPSTREAM
        # --------------------------------------------------

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
                logger.warning(
                    "tjrs_known_error",
                    extra={
                        "request_id": request_id,
                        "npu": npu_digits20,
                        "error_type": (
                            type(response).__name__
                        ),
                    },
                )

                raise response

            if isinstance(
                response,
                Exception,
            ):
                logger.exception(
                    "tjrs_unexpected_error",
                    extra={
                        "request_id": request_id,
                        "npu": npu_digits20,
                        "error_type": (
                            type(response).__name__
                        ),
                    },
                    exc_info=(
                        type(response),
                        response,
                        response.__traceback__,
                    ),
                )

                raise TJRSUpstreamError(
                    "Erro inesperado durante "
                    "a consulta ao TJRS: "
                    f"{type(response).__name__}"
                ) from response

        # --------------------------------------------------
        # PARSING
        # --------------------------------------------------

        parse_started_at = time.perf_counter()

        try:
            basic_data = (
                self.crawler
                .extract_basic_data_partes(
                    basic_data_response
                )
            )

            movimentos = (
                self.crawler.extract_movimentos(
                    movimentos_response
                )
            )

        except Exception as exc:
            logger.exception(
                "tjrs_parse_failed",
                extra={
                    "request_id": request_id,
                    "npu": npu_digits20,
                    "error_type": (
                        type(exc).__name__
                    ),
                },
            )

            raise TJRSParseError(
                "Falha ao processar a resposta "
                "do TJRS: "
                f"{type(exc).__name__}"
            ) from exc

        parse_duration_ms = (
            time.perf_counter()
            - parse_started_at
        ) * 1000

        logger.info(
            "tjrs_parse_completed",
            extra={
                "request_id": request_id,
                "npu": npu_digits20,
                "duration_ms": round(
                    parse_duration_ms,
                    2,
                ),
                "movimentos_count": len(
                    movimentos
                ),
            },
        )

        # --------------------------------------------------
        # PROCESSO NÃO ENCONTRADO
        # --------------------------------------------------

        if not basic_data:
            logger.warning(
                "process_not_found",
                extra={
                    "request_id": request_id,
                    "npu": npu_digits20,
                },
            )

            raise ProcessNotFoundError(
                "TJRS não retornou dados para "
                "o processo informado."
            )

        # --------------------------------------------------
        # RESULTADO
        # --------------------------------------------------

        results = {
            **basic_data,
            "movimentos": movimentos,
        }

        # --------------------------------------------------
        # CACHE WRITE
        # --------------------------------------------------

        try:
            await set_cache(
                cache_key,
                results,
            )

            logger.info(
                "process_cache_written",
                extra={
                    "request_id": request_id,
                    "npu": npu_digits20,
                    "cache_key": cache_key,
                },
            )

        except Exception:
            logger.exception(
                "process_cache_write_failed",
                extra={
                    "request_id": request_id,
                    "cache_key": cache_key,
                    "npu": npu_digits20,
                },
            )

        # --------------------------------------------------
        # FINAL
        # --------------------------------------------------

        total_duration_ms = (
            time.perf_counter()
            - started_at
        ) * 1000

        logger.info(
            "process_search_completed",
            extra={
                "request_id": request_id,
                "npu": npu_digits20,
                "source": "tjrs",
                "duration_ms": round(
                    total_duration_ms,
                    2,
                ),
            },
        )

        return results
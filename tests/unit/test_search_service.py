import json

import pytest

from api.exceptions import ProcessNotFoundError
from crawler_jus.services.search_service import SearchService

NPU = "5001646-66.2026.8.21.0008"


class FakeCrawlerSemProcesso:
    async def request_page(
        self,
        url: str,
    ) -> str:
        return json.dumps({"data": []})

    def extract_basic_data_partes(
        self,
        text: str,
    ) -> dict:
        return {}

    def extract_movimentos(
        self,
        text: str,
    ) -> list:
        return []


@pytest.mark.asyncio
async def test_search_service_deve_lancar_process_not_found(
    monkeypatch,
):
    crawler = FakeCrawlerSemProcesso()

    service = SearchService(crawler)

    async def fake_get_cache(
        cache_key: str,
    ):
        return None

    async def fake_set_cache(
        cache_key: str,
        value: dict,
        ttl: int,
    ):
        return None

    monkeypatch.setattr(
        "crawler_jus.services.search_service.get_cache",
        fake_get_cache,
    )

    monkeypatch.setattr(
        "crawler_jus.services.search_service.set_cache",
        fake_set_cache,
    )

    with pytest.raises(ProcessNotFoundError):
        await service.search_npu(NPU)

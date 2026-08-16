import pytest

from httpx import (
    AsyncClient,
    ASGITransport,
)
from api.exceptions import (
    ProcessNotFoundError,
    TJRSParseError,
    TJRSRateLimit,
)
from api.router import app

NPU = "5001646-66.2026.8.21.0008"


class FakeSearchService:
    async def search_npu(
        self,
        npu: str,
        force_refresh: bool = False,
    ):
        return {
            "npu": npu,
            "status": "ok",
        }


class RateLimitSearchService:
    async def search_npu(
        self,
        npu: str,
        force_refresh: bool = False,
    ):
        raise TJRSRateLimit(
            "Limite",
            retry_after=30,
        )


class NotFoundSearchService:
    async def search_npu(
        self,
        npu: str,
        force_refresh: bool = False,
    ):
        raise ProcessNotFoundError("Processo não encontrado")


class ParseErrorSearchService:
    async def search_npu(
        self,
        npu: str,
        force_refresh: bool = False,
    ):
        raise TJRSParseError("Falha ao interpretar resposta do TJRS")


@pytest.fixture
def set_search_service():
    old_service = getattr(
        app.state,
        "search_service",
        None,
    )

    def _set(service):
        app.state.search_service = service

    yield _set

    if old_service is None:
        if hasattr(
            app.state,
            "search_service",
        ):
            del app.state._state["search_service"]
    else:
        app.state.search_service = old_service


@pytest.mark.asyncio
async def test_search_npu_success(
    set_search_service,
):
    set_search_service(FakeSearchService())

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/search_npu",
            json={
                "npu": NPU,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["npu"] == NPU
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_search_npu_rate_limit(
    set_search_service,
):
    set_search_service(RateLimitSearchService())

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/search_npu",
            json={
                "npu": NPU,
            },
        )

    assert response.status_code == 429

    data = response.json()

    assert data["error"] == "TJRSRateLimit"
    assert data["detail"] == "Limite"


@pytest.mark.asyncio
async def test_search_npu_deve_retornar_404_quando_processo_nao_existe(
    set_search_service,
):
    set_search_service(NotFoundSearchService())

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/search_npu",
            json={
                "npu": NPU,
            },
        )

    assert response.status_code == 404

    data = response.json()

    assert data["error"] == "ProcessNotFoundError"
    assert data["detail"] == "Processo não encontrado"


@pytest.mark.asyncio
async def test_search_npu_deve_retornar_502_em_erro_de_parse(
    set_search_service,
):
    set_search_service(ParseErrorSearchService())

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/search_npu",
            json={
                "npu": NPU,
            },
        )

    assert response.status_code == 502

    data = response.json()

    assert data["error"] == "TJRSParseError"

    assert data["detail"] == "Falha ao interpretar resposta do TJRS"

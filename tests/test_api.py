import json
import pytest
from httpx import AsyncClient, ASGITransport
from api.router import app
from api.exceptions import TJRSRateLimit
from crawler_jus.crawler import Crawler
from crawler_jus.services import search_service
from unittest.mock import AsyncMock


class FakeCrawler:
    async def request_page(self, url: str) -> str:
        if "consultaProcesso" in url:
            return json.dumps(
                {
                    "data": [
                        {
                            "nomeClasse": "CUMPRIMENTO DE SENTENÇA",
                            "nomeNatureza": "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL",
                            "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
                            "assuntoCNJ": "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL",
                            "partes": {
                                "parte": [
                                    {
                                        "descricaoTipo": "EXEQUENTE",
                                        "nome": "UNIFERTIL - UNIVERSAL DE FERTILIZANTES S/A",
                                    }
                                ]
                            },
                        }
                    ]
                }
            )
        return json.dumps(
            {
                "data": [
                    {
                        "data": "23/01/2026",
                        "descricao": "Expedida/certificada a intimação eletrônica",
                    }
                ]
            }
        )

    transport = ASGITransport(app=app)

    def extract_basic_data_partes(self, text: str):
        return Crawler().extract_basic_data_partes(text)

    def extract_movimentos(self, text: str):
        return Crawler().extract_movimentos(text)


@pytest.mark.asyncio
async def test_search_npu_success(monkeypatch):
    app.state.crawler = FakeCrawler()
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/search_npu", json={"npu": "5001646-66.2026.8.21.0008"}
        )
    assert response.status_code == 200
    body = response.json()
    assert "movimentos" in body
    assert body["nomeClasse"] == "CUMPRIMENTO DE SENTENÇA"


@pytest.mark.asyncio
async def test_search_npu_rate_limit(monkeypatch):
    transport = ASGITransport(app=app)

    class Rate_limit:
        async def request_page(self, url: str) -> str:
            raise TJRSRateLimit("Limite", retry_after=30)

    app.state.crawler = Rate_limit()
    monkeypatch.setattr(search_service, "get_cache", AsyncMock(return_value=None))
    monkeypatch.setattr(search_service, "set_cache", AsyncMock(return_value=None))

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/search_npu", json={"npu": "5001646-66.2026.8.21.0008"}
        )
    assert response.status_code == 429
    assert response.headers.get("retry-after") == "30"

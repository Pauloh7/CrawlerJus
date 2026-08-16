import pytest
from langchain_core.messages import ToolMessage

from crawler_jus.crawler import Crawler
from crawler_jus.services.search_service import SearchService
from legal_ai.legacy.simple_agent import create_legal_agent


@pytest.mark.asyncio
async def test_agent_deve_consultar_processo():
    crawler = Crawler()

    try:
        service = SearchService(crawler)
        agent = create_legal_agent(service)

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Quais são as partes do processo "
                            "5001646-66.2026.8.21.0008?"
                        ),
                    }
                ]
            }
        )

        tool_messages = [
            message
            for message in result["messages"]
            if isinstance(message, ToolMessage)
        ]

        assert len(tool_messages) > 0

    finally:
        await crawler.close()


@pytest.mark.asyncio
async def test_agent_nao_deve_consultar_processo():
    crawler = Crawler()

    try:
        service = SearchService(crawler)
        agent = create_legal_agent(service)

        result = await agent.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": ("O que significa conclusão para decisão?"),
                    }
                ]
            }
        )

        tool_messages = [
            message
            for message in result["messages"]
            if isinstance(message, ToolMessage)
        ]

        assert len(tool_messages) == 0

    finally:
        await crawler.close()

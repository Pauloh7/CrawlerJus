import asyncio

from legal_ai.graph import create_legal_graph
from crawler_jus.crawler import Crawler
from crawler_jus.services.search_service import SearchService


async def main():
    crawler = Crawler()

    try:
        service = SearchService(crawler)

        graph = create_legal_graph(service)

        config = {"configurable": {"thread_id": "teste-1"}}

        print("\nPRIMEIRA PERGUNTA")

        result1 = await graph.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Consulte o processo "
                            "5001646-66.2026.8.21.0008 "
                            "e me diga qual é a classe."
                        ),
                    }
                ]
            },
            config=config,
        )

        print(result1["messages"][-1].content)

        print("\nSTATE APÓS PRIMEIRA PERGUNTA")
        print("NPU:", result1.get("npu"))
        print("LLM calls:", result1.get("llm_calls"))
        print("Tool calls:", result1.get("tool_calls_count"))
        print("TJRS calls:", result1.get("external_calls_count"))
        print("Cache hits:", result1.get("cache_hits"))

        print("\nSEGUNDA PERGUNTA")

        result2 = await graph.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": ("E quais são as partes dele?"),
                    }
                ]
            },
            config=config,
        )

        print(result2["messages"][-1].content)

        print("\nSTATE APÓS SEGUNDA PERGUNTA")
        print("NPU:", result2.get("npu"))
        print("LLM calls:", result2.get("llm_calls"))
        print("Tool calls:", result2.get("tool_calls_count"))
        print("TJRS calls:", result2.get("external_calls_count"))
        print("Cache hits:", result2.get("cache_hits"))

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())

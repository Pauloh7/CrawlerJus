import asyncio
from unittest import result

from legal_ai.graph import create_legal_graph
from crawler_jus.crawler import Crawler
from crawler_jus.services.search_service import SearchService


async def main():
    crawler = Crawler()

    try:
        service = SearchService(crawler)

        graph = create_legal_graph(service)

        result = await graph.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Quais são as últimas "
                            "movimentações do processo "
                            "5001646-66.2026.8.21.0008?"
                        ),
                    }
                ],
                "llm_calls": 0,
                "tool_calls_count": 0,
            }
        )

        for message in result["messages"]:
            print("\n" + "=" * 80)
            print(type(message).__name__)

            print("CONTENT:")
            print(message.content)

            if hasattr(message, "tool_calls"):
                print("TOOL CALLS:")
                print(message.tool_calls)
        print("LLM CALLS:", result["llm_calls"])
        print("TOOL CALLS:", result["tool_calls_count"])
        print("\n" + "=" * 80)

        print(
            "NPU:",
            result.get("npu"),
        )

        print(
            "LLM CALLS:",
            result.get("llm_calls"),
        )

        print(
            "TOOL CALLS:",
            result.get("tool_calls_count"),
        )

        print(
            "PROCESS DATA EXISTE:",
            result.get("process_data") is not None,
        )

    finally:
        await crawler.close()


asyncio.run(main())

import asyncio
from langchain_core.messages import ToolMessage
from legal_ai.agent import create_legal_agent
from crawler_jus.crawler import Crawler
from crawler_jus.services.search_service import SearchService

TESTES = [
    "Quais foram as últimas movimentações do processo " "5001646-66.2026.8.21.0008?",
    "Quais são as partes do processo " "5001646-66.2026.8.21.0008?",
    "Explique de forma simples o que aconteceu no processo "
    "5001646-66.2026.8.21.0008.",
    "O que significa conclusão para decisão?",
]


async def main():
    crawler = Crawler()

    try:
        service = SearchService(crawler)
        agent = create_legal_agent(service)

        for i, pergunta in enumerate(TESTES, start=1):
            result = await agent.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": pergunta,
                        }
                    ]
                }
            )

            tool_messages = [
                message
                for message in result["messages"]
                if isinstance(message, ToolMessage)
            ]

            print("\nPERGUNTA:")
            print(pergunta)

            print("\nCHAMOU TOOL:")
            print(bool(tool_messages))

            print("\nRESPOSTA:")
            print(result["messages"][-1].content)

    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())

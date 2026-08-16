import pytest

from langgraph.checkpoint.memory import InMemorySaver

from crawler_jus.crawler import Crawler
from crawler_jus.services.search_service import SearchService
from legal_ai.graph import create_legal_graph

from tests.evals.cases import NPU


MULTITURN_CASES = [
    {
        "id": "classe_depois_partes",
        "turns": [
            {
                "question": (
                    f"Consulte o processo {NPU} "
                    "e me diga a classe."
                ),
            },
            {
                "question": (
                    "E quais são as partes dele?"
                ),
                "answer_contains": [
                    "UNIFERTIL",
                    "BANCO BRADESCO",
                ],
            },
        ],
        "expected_npu": NPU,
        "expected_external_calls": 1,
    }
]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    MULTITURN_CASES,
    ids=lambda case: case["id"],
)
async def test_agent_eval_multiturn(case):
    crawler = Crawler()

    try:
        service = SearchService(crawler)

        graph = create_legal_graph(
            service=service,
            checkpointer=InMemorySaver(),
        )

        config = {
            "configurable": {
                "thread_id": (
                    f"eval-multiturn-{case['id']}"
                )
            }
        }

        result = None

        for turn in case["turns"]:
            result = await graph.ainvoke(
                {
                    "messages": [
                        {
                            "role": "user",
                            "content": turn["question"],
                        }
                    ]
                },
                config=config,
            )

            answer_contains = turn.get(
                "answer_contains",
                [],
            )

            answer = (
                result["messages"][-1]
                .content
                .upper()
            )

            for expected_text in answer_contains:
                assert expected_text.upper() in answer

        assert result is not None

        assert (
            result.get("npu")
            == case["expected_npu"]
        )

        assert (
            result.get(
                "external_calls_count",
                0,
            )
            == case[
                "expected_external_calls"
            ]
        )

    finally:
        await crawler.close()
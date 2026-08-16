import pytest
from langgraph.checkpoint.memory import InMemorySaver

from crawler_jus.crawler import Crawler
from crawler_jus.services.search_service import SearchService
from legal_ai.graph import create_legal_graph
from tests.evals.cases import EVAL_CASES


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "case",
    EVAL_CASES,
    ids=lambda case: case["id"],
)
async def test_agent_eval_matrix(case):
    crawler = Crawler()

    try:
        service = SearchService(crawler)

        graph = create_legal_graph(
            service=service,
            checkpointer=InMemorySaver(),
        )

        result = await graph.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": case["question"],
                    }
                ]
            },
            config={
                "configurable": {
                    "thread_id": f"eval-{case['id']}"
                }
            },
        )

        answer = result["messages"][-1].content.upper()

        assert result.get("npu") == case["expected_npu"]

        assert (
            result.get("external_calls_count", 0)
            <= case["max_external_calls"]
        )

        assert (
            result.get("tool_calls_count", 0)
            == case["expected_tool_calls"]
        )

        for expected_text in case["answer_contains"]:
            assert expected_text.upper() in answer

    finally:
        await crawler.close()
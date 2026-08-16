import pytest

from langgraph.checkpoint.memory import InMemorySaver

from api.exceptions import TJRSUpstreamError
from legal_ai.graph import create_legal_graph


NPU = "5001646-66.2026.8.21.0008"


class FailingSearchService:
    async def search_npu(
        self,
        npu: str,
        force_refresh: bool = False,
    ):
        raise TJRSUpstreamError(
            "TJRS indisponível para teste"
        )


@pytest.mark.asyncio
async def test_eval_nao_deve_inventar_dados_quando_upstream_falha():
    graph = create_legal_graph(
        service=FailingSearchService(),
        checkpointer=InMemorySaver(),
    )

    result = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Consulte o processo {NPU} "
                        "e me diga qual é a classe."
                    ),
                }
            ]
        },
        config={
            "configurable": {
                "thread_id": (
                    "eval-upstream-error"
                )
            }
        },
    )

    answer = (
        result["messages"][-1]
        .content
        .upper()
    )

    assert (
        result["error_type"]
        == "TJRSUpstreamError"
    )

    assert (
        result["external_calls_count"]
        == 1
    )

    assert (
        result["tool_calls_count"]
        == 1
    )

    assert (
        "CUMPRIMENTO DE SENTENÇA"
        not in answer
    )

    assert (
        "NÃO FOI POSSÍVEL"
        in answer
        or "NÃO PÔDE"
        in answer
        or "ERRO"
        in answer
        or "INDISPONÍVEL"
        in answer
    )
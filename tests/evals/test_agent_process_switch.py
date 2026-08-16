import pytest
from langgraph.checkpoint.memory import InMemorySaver

from legal_ai.graph import create_legal_graph

NPU_A = "5001646-66.2026.8.21.0008"
NPU_B = "5001983-12.2013.8.21.0008"


class FakeSearchService:
    def __init__(self):
        self.calls = []

    async def search_npu(
        self,
        npu: str,
        force_refresh: bool = False,
    ):
        self.calls.append(npu)

        if npu == NPU_A:
            return {
                "numeroProcesso": NPU_A,
                "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
                "assuntoCNJ": "DIREITO CIVIL",
                "partes": [
                    {
                        "descricaoTipo": "EXEQUENTE",
                        "nome": "PARTE PROCESSO A",
                    }
                ],
                "movimentos": [],
            }

        if npu == NPU_B:
            return {
                "numeroProcesso": NPU_B,
                "classeCNJ": "PROCEDIMENTO COMUM",
                "assuntoCNJ": "DIREITO CIVIL",
                "partes": [
                    {
                        "descricaoTipo": "AUTOR",
                        "nome": "PARTE PROCESSO B",
                    }
                ],
                "movimentos": [],
            }

        raise ValueError(
            f"NPU não esperado no eval: {npu}"
        )


@pytest.mark.asyncio
async def test_eval_deve_trocar_processo_na_mesma_thread():
    service = FakeSearchService()

    graph = create_legal_graph(
        service=service,
        checkpointer=InMemorySaver(),
    )

    config = {
        "configurable": {
            "thread_id": "eval-switch-process"
        }
    }

    result_a = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Consulte o processo {NPU_A} "
                        "e me diga qual é a classe."
                    ),
                }
            ]
        },
        config=config,
    )

    assert result_a["npu"] == NPU_A
    assert service.calls == [NPU_A]

    result_b = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Agora consulte o processo {NPU_B} "
                        "e me diga qual é a classe."
                    ),
                }
            ]
        },
        config=config,
    )

    answer = (
        result_b["messages"][-1]
        .content
        .upper()
    )

    assert result_b["npu"] == NPU_B

    assert service.calls == [
        NPU_A,
        NPU_B,
    ]

    assert (
        "PROCEDIMENTO COMUM"
        in answer
    )

    assert result_b[
        "external_calls_count"
    ] == 2

    assert result_b[
        "cache_hits"
    ] == 0
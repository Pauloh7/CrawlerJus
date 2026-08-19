import pytest
from langchain.messages import (
    AIMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.memory import InMemorySaver

from legal_ai.graph import create_legal_graph

NPU = "5001646-66.2026.8.21.0008"
NPU_2 = "5001983-12.2013.8.21.0008"


class FakeSearchService:
    def __init__(self):
        self.calls = []

    async def search_npu(
        self,
        npu: str,
        force_refresh: bool = False,
    ):
        self.calls.append(npu)

        return {
            "numeroProcesso": npu,
            "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
            "partes": [
                {
                    "descricaoTipo": "EXEQUENTE",
                    "nome": "UNIFERTIL",
                }
            ],
        }


class FakeModelWithTools:
    def __init__(self, responses):
        self.responses = iter(responses)

    def bind_tools(self, tools):
        async def fake_invoke(messages):
            return next(self.responses)

        return RunnableLambda(fake_invoke)


@pytest.mark.asyncio
async def test_legal_graph_deve_executar_fluxo_completo():
    service = FakeSearchService()

    model = FakeModelWithTools(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {
                            "npu": NPU,
                        },
                        "id": "tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content=("A classe do processo é " "CUMPRIMENTO DE SENTENÇA.")),
        ]
    )

    checkpointer = InMemorySaver()

    graph = create_legal_graph(
        service=service,
        checkpointer=checkpointer,
        model=model,
    )

    config = {"configurable": {"thread_id": "test-graph-1"}}

    result = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (f"Consulte o processo {NPU} " "e me diga a classe."),
                }
            ]
        },
        config=config,
    )

    assert service.calls == [NPU]

    assert result["npu"] == NPU

    assert result["process_data"]["classeCNJ"] == "CUMPRIMENTO DE SENTENÇA"

    assert result["llm_calls"] == 2
    assert result["tool_calls_count"] == 1
    assert result["external_calls_count"] == 1
    assert result["cache_hits"] == 0

    tool_messages = [
        message
        for message in result["messages"]
        if isinstance(
            message,
            ToolMessage,
        )
    ]

    assert len(tool_messages) == 1

    assert result["messages"][-1].content == (
        "A classe do processo é " "CUMPRIMENTO DE SENTENÇA."
    )
    assert (
        result["active_skill"]
        == "consulta-processual"
    )

@pytest.mark.asyncio
async def test_legal_graph_deve_finalizar_sem_tool_call():
    service = FakeSearchService()

    model = FakeModelWithTools(
        responses=[
            AIMessage(
                content=(
                    "Conclusão para decisão significa "
                    "que o processo está com o juiz."
                )
            )
        ]
    )

    graph = create_legal_graph(
        service=service,
        checkpointer=InMemorySaver(),
        model=model,
    )

    result = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": ("O que significa conclusão " "para decisão?"),
                }
            ]
        },
        config={"configurable": {"thread_id": "test-sem-tool"}},
    )

    assert service.calls == []

    assert result["llm_calls"] == 1

    assert result["messages"][-1].content == (
        "Conclusão para decisão significa " "que o processo está com o juiz."
    )

    assert result.get("tool_calls_count") is None
    assert result.get("external_calls_count") is None


@pytest.mark.asyncio
async def test_legal_graph_deve_reutilizar_cache_do_checkpoint():
    service = FakeSearchService()

    model = FakeModelWithTools(
        responses=[
            # 1ª execução - agent pede a tool
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {
                            "npu": NPU,
                        },
                        "id": "tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
            # 1ª execução - resposta final
            AIMessage(content=("A classe é " "CUMPRIMENTO DE SENTENÇA.")),
            # 2ª execução - agent pede
            # a mesma tool novamente
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {
                            "npu": NPU,
                        },
                        "id": "tool-2",
                        "type": "tool_call",
                    }
                ],
            ),
            # 2ª execução - resposta final
            AIMessage(content=("A parte exequente é UNIFERTIL.")),
        ]
    )

    checkpointer = InMemorySaver()

    graph = create_legal_graph(
        service=service,
        checkpointer=checkpointer,
        model=model,
    )

    config = {"configurable": {"thread_id": "test-cache-1"}}

    # -------------------------
    # PRIMEIRA EXECUÇÃO
    # -------------------------

    result1 = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (f"Consulte o processo {NPU} " "e me diga a classe."),
                }
            ]
        },
        config=config,
    )

    # Houve consulta externa
    assert service.calls == [NPU]

    assert result1["external_calls_count"] == 1
    assert result1["tool_calls_count"] == 1
    assert result1["cache_hits"] == 0

    # -------------------------
    # SEGUNDA EXECUÇÃO
    # -------------------------

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

    # IMPORTANTE:
    # ainda deve existir apenas UMA
    # chamada ao FakeSearchService.
    assert service.calls == [NPU]

    # O modelo pediu tool pela segunda vez
    assert result2["tool_calls_count"] == 2

    # Mas chamada externa continua em 1
    assert result2["external_calls_count"] == 1

    # O segundo acesso foi atendido pelo cache
    assert result2["cache_hits"] == 1

    # O NPU continuou persistido
    assert result2["npu"] == NPU

    # O dado do processo também continua no state
    assert result2["process_data"]["classeCNJ"] == "CUMPRIMENTO DE SENTENÇA"

    # Resposta final da segunda execução
    assert result2["messages"][-1].content == "A parte exequente é UNIFERTIL."


@pytest.mark.asyncio
async def test_legal_graph_deve_trocar_npu_na_mesma_thread():
    service = FakeSearchService()

    model = FakeModelWithTools(
        responses=[
            # Primeira pergunta:
            # consulta NPU original
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {
                            "npu": NPU,
                        },
                        "id": "tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Primeiro processo consultado."),
            # Segunda pergunta:
            # usuário informa explicitamente outro NPU
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {
                            "npu": NPU_2,
                        },
                        "id": "tool-2",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Segundo processo consultado."),
        ]
    )

    graph = create_legal_graph(
        service=service,
        checkpointer=InMemorySaver(),
        model=model,
    )

    config = {"configurable": {"thread_id": "test-troca-npu"}}

    # Primeira consulta
    result1 = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (f"Consulte o processo {NPU}."),
                }
            ]
        },
        config=config,
    )

    assert result1["npu"] == NPU
    assert service.calls == [NPU]

    # Segunda consulta, MESMA THREAD,
    # mas NPU explicitamente diferente.
    result2 = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (f"Agora consulte o processo {NPU_2}."),
                }
            ]
        },
        config=config,
    )

    # O novo NPU precisa substituir o anterior.
    assert result2["npu"] == NPU_2

    # Como é outro processo, não pode usar
    # process_data do primeiro como cache.
    assert service.calls == [
        NPU,
        NPU_2,
    ]

    assert result2["tool_calls_count"] == 2

    # Foram necessárias duas consultas externas:
    # uma para cada processo.
    assert result2["external_calls_count"] == 2

    # Não houve cache hit.
    assert result2["cache_hits"] == 0

    assert result2["messages"][-1].content == "Segundo processo consultado."


@pytest.mark.asyncio
async def test_legal_graph_npu_invalido_nao_deve_chamar_service():
    service = FakeSearchService()

    invalid_npu = "123"

    model = FakeModelWithTools(
        responses=[
            # O modelo pede a tool com NPU inválido.
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {
                            "npu": invalid_npu,
                        },
                        "id": "tool-invalid",
                        "type": "tool_call",
                    }
                ],
            ),
            # Depois que search_process retorna
            # ToolMessage de erro, o agent responde.
            AIMessage(content=("O número do processo informado " "é inválido.")),
        ]
    )

    graph = create_legal_graph(
        service=service,
        checkpointer=InMemorySaver(),
        model=model,
    )

    result = await graph.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": ("Consulte o processo 123."),
                }
            ]
        },
        config={"configurable": {"thread_id": "test-npu-invalido"}},
    )

    # O SearchService nunca pode ser chamado.
    assert service.calls == []

    assert result["error_type"] == "INVALID_NPU"

    assert result["error"] == "NPU inválido: 123"

    # O modelo solicitou a tool.
    assert result["tool_calls_count"] == 1

    # Mas não houve chamada externa.
    assert (
        result.get(
            "external_calls_count",
            0,
        )
        == 0
    )

    assert (
        result.get(
            "cache_hits",
            0,
        )
        == 0
    )

    # Houve duas chamadas ao modelo:
    # 1. tool call
    # 2. resposta após receber o erro
    assert result["llm_calls"] == 2

    assert result["messages"][-1].content == (
        "O número do processo informado " "é inválido."
    )

import os
import uuid

import pytest

from dotenv import load_dotenv
from langchain.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from legal_ai.graph import create_legal_graph

load_dotenv()

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
async def test_checkpoint_postgres_deve_persistir_state():
    db_url = os.getenv("LANGGRAPH_DB_URL")

    assert db_url is not None

    thread_id = f"integration-{uuid.uuid4()}"

    service = FakeSearchService()

    # ----------------------------------
    # PRIMEIRA INSTÂNCIA DO GRAFO
    # ----------------------------------

    model1 = FakeModelWithTools(
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
            AIMessage(content=("A classe é " "CUMPRIMENTO DE SENTENÇA.")),
        ]
    )

    async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer1:

        await checkpointer1.setup()

        graph1 = create_legal_graph(
            service=service,
            checkpointer=checkpointer1,
            model=model1,
        )

        config = {"configurable": {"thread_id": thread_id}}

        result1 = await graph1.ainvoke(
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

    # Aqui a conexão/checkpointer1 fechou.

    # ----------------------------------
    # SEGUNDA INSTÂNCIA DO GRAFO
    # ----------------------------------

    model2 = FakeModelWithTools(
        responses=[AIMessage(content=("A parte exequente é UNIFERTIL."))]
    )

    async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer2:

        graph2 = create_legal_graph(
            service=service,
            checkpointer=checkpointer2,
            model=model2,
        )

        result2 = await graph2.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": ("E quem é o exequente?"),
                    }
                ]
            },
            config=config,
        )

    assert result2["npu"] == NPU

    assert result2["process_data"]["classeCNJ"] == "CUMPRIMENTO DE SENTENÇA"

    assert result2["llm_calls"] == 3

    # Só houve uma consulta ao fake service.
    assert service.calls == [NPU]

    assert result2["messages"][-1].content == "A parte exequente é UNIFERTIL."


@pytest.mark.asyncio
async def test_checkpoint_postgres_deve_isolar_threads():
    db_url = os.getenv("LANGGRAPH_DB_URL")

    assert db_url is not None

    service = FakeSearchService()

    thread_a = f"integration-a-{uuid.uuid4()}"
    thread_b = f"integration-b-{uuid.uuid4()}"

    model_a = FakeModelWithTools(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {
                            "npu": NPU,
                        },
                        "id": "tool-a",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="Processo A consultado."),
        ]
    )

    async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:

        graph_a = create_legal_graph(
            service=service,
            checkpointer=checkpointer,
            model=model_a,
        )

        result_a = await graph_a.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (f"Consulte o processo {NPU}."),
                    }
                ]
            },
            config={"configurable": {"thread_id": thread_a}},
        )

        assert result_a["npu"] == NPU

    # Nova instância do checkpointer/grafo
    model_b = FakeModelWithTools(
        responses=[AIMessage(content=("Informe o número do processo."))]
    )

    async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:

        graph_b = create_legal_graph(
            service=service,
            checkpointer=checkpointer,
            model=model_b,
        )

        result_b = await graph_b.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": ("E quais são as partes dele?"),
                    }
                ]
            },
            config={"configurable": {"thread_id": thread_b}},
        )

    # Thread B não pode herdar o NPU da thread A
    assert result_b.get("npu") is None

    assert result_b.get("process_data") is None

    assert result_b["messages"][-1].content == "Informe o número do processo."

    # Só a thread A chamou o service
    assert service.calls == [NPU]


@pytest.mark.asyncio
async def test_checkpoint_postgres_deve_persistir_troca_de_npu():
    db_url = os.getenv("LANGGRAPH_DB_URL")

    assert db_url is not None

    thread_id = f"integration-switch-{uuid.uuid4()}"

    service = FakeSearchService()

    # -------------------------
    # PRIMEIRO PROCESSO
    # -------------------------

    model1 = FakeModelWithTools(
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
            AIMessage(content="Primeiro processo consultado."),
        ]
    )

    async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer1:

        graph1 = create_legal_graph(
            service=service,
            checkpointer=checkpointer1,
            model=model1,
        )

        config = {"configurable": {"thread_id": thread_id}}

        result1 = await graph1.ainvoke(
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

    # -------------------------
    # SEGUNDO PROCESSO
    # MESMA THREAD
    # -------------------------

    model2 = FakeModelWithTools(
        responses=[
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

    async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer2:

        graph2 = create_legal_graph(
            service=service,
            checkpointer=checkpointer2,
            model=model2,
        )

        result2 = await graph2.ainvoke(
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

        assert result2["npu"] == NPU_2

    # -------------------------
    # TERCEIRA INSTÂNCIA
    # CONFIRMA O ESTADO NOVO
    # -------------------------

    model3 = FakeModelWithTools(
        responses=[AIMessage(content=("O processo atual é o segundo."))]
    )

    async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer3:

        graph3 = create_legal_graph(
            service=service,
            checkpointer=checkpointer3,
            model=model3,
        )

        result3 = await graph3.ainvoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": ("Qual é o processo atual?"),
                    }
                ]
            },
            config=config,
        )

    # O estado persistido agora deve ser NPU_2
    assert result3["npu"] == NPU_2

    assert result3["process_data"]["numeroProcesso"] == NPU_2

    # Cada processo foi consultado uma vez
    assert service.calls == [
        NPU,
        NPU_2,
    ]

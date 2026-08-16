import pytest

from api.exceptions import TJRSUpstreamError
from langchain.messages import (
    AIMessage,
    HumanMessage,
)

from legal_ai.nodes import search_process

NPU = "5001646-66.2026.8.21.0008"


class FakeTool:
    def __init__(self):
        self.calls = []

    async def ainvoke(self, args):
        self.calls.append(args)

        return {
            "numeroProcesso": args["npu"],
            "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
        }


class FailingTool:
    async def ainvoke(self, args):
        raise TJRSUpstreamError("TJRS fora do ar")


class BuggyTool:
    async def ainvoke(self, args):
        raise RuntimeError("Bug inesperado")


@pytest.mark.asyncio
async def test_search_process_deve_chamar_tool_sem_cache():
    tool = FakeTool()

    state = {
        "messages": [
            HumanMessage(content=(f"Consulte o processo {NPU}")),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {"npu": NPU},
                        "id": "tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
        ],
        "tool_calls_count": 0,
        "external_calls_count": 0,
        "cache_hits": 0,
    }

    result = await search_process(
        state,
        {"consultar_processo": tool},
    )

    assert len(tool.calls) == 1
    assert tool.calls[0]["npu"] == NPU

    assert result["npu"] == NPU
    assert result["process_data"]["classeCNJ"] == ("CUMPRIMENTO DE SENTENÇA")

    assert result["external_calls_count"] == 1
    assert result["tool_calls_count"] == 1
    assert result["cache_hits"] == 0

    assert result["error"] is None
    assert result["error_type"] is None


@pytest.mark.asyncio
async def test_search_process_deve_usar_cache():
    tool = FakeTool()

    process_data = {
        "numeroProcesso": NPU,
        "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
    }

    state = {
        "messages": [
            HumanMessage(content="Quais são as partes dele?"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {"npu": NPU},
                        "id": "tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
        ],
        "npu": NPU,
        "process_data": process_data,
        "tool_calls_count": 1,
        "external_calls_count": 1,
        "cache_hits": 0,
    }

    result = await search_process(
        state,
        {"consultar_processo": tool},
    )

    # Não pode acessar a tool externa
    assert len(tool.calls) == 0

    assert result["process_data"] == process_data
    assert result["external_calls_count"] == 1
    assert result["cache_hits"] == 1
    assert result["tool_calls_count"] == 2


@pytest.mark.asyncio
async def test_search_process_nao_deve_chamar_tool_com_npu_invalido():
    tool = FakeTool()

    state = {
        "messages": [
            HumanMessage(content="Consulte o processo 123"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {"npu": "123"},
                        "id": "tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
        ]
    }

    result = await search_process(
        state,
        {"consultar_processo": tool},
    )

    assert len(tool.calls) == 0
    assert result["error_type"] == "INVALID_NPU"
    assert result["tool_calls_count"] == 1


@pytest.mark.asyncio
async def test_search_process_deve_tratar_erro_da_tool():
    tool = FailingTool()

    state = {
        "messages": [
            HumanMessage(content=f"Consulte o processo {NPU}"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {"npu": NPU},
                        "id": "tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
        ],
        "external_calls_count": 0,
        "tool_calls_count": 0,
        "cache_hits": 0,
    }

    result = await search_process(
        state,
        {"consultar_processo": tool},
    )

    assert result["error_type"] == ("TJRSUpstreamError")

    assert result["external_calls_count"] == 1
    assert result["tool_calls_count"] == 1
    assert result["cache_hits"] == 0


@pytest.mark.asyncio
async def test_search_process_deve_rejeitar_tool_desconhecida():
    state = {
        "messages": [
            HumanMessage(content=f"Consulte o processo {NPU}"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "tool_que_nao_existe",
                        "args": {"npu": NPU},
                        "id": "tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
        ],
    }

    result = await search_process(
        state,
        {},
    )

    assert result["error_type"] == "UNKNOWN_TOOL"
    assert result["tool_calls_count"] == 1


@pytest.mark.asyncio
async def test_search_process_nao_deve_esconder_erro_inesperado():
    tool = BuggyTool()

    state = {
        "messages": [
            HumanMessage(content=f"Consulte o processo {NPU}"),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {"npu": NPU},
                        "id": "tool-1",
                        "type": "tool_call",
                    }
                ],
            ),
        ]
    }

    with pytest.raises(
        RuntimeError,
        match="Bug inesperado",
    ):
        await search_process(
            state,
            {"consultar_processo": tool},
        )

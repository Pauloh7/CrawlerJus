from langchain.messages import AIMessage
from langgraph.graph import END

from legal_ai.nodes import should_continue


def test_should_continue_deve_ir_para_search_process():
    state = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "consultar_processo",
                        "args": {"npu": "5001646-66.2026.8.21.0008"},
                        "id": "tool-1",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    }

    result = should_continue(state)

    assert result == "search_process"


def test_should_continue_deve_finalizar_sem_tool_call():
    state = {
        "messages": [
            AIMessage(content=("A classe do processo é " "CUMPRIMENTO DE SENTENÇA."))
        ]
    }

    result = should_continue(state)

    assert result == END

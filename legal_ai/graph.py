from typing import Literal

from langchain.messages import ToolMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from legal_ai.state import AgentState
from legal_ai.tools import create_process_tools

from crawler_jus.services.search_service import (
    SearchService,
)


SYSTEM_PROMPT = """
Você é um assistente especializado em
processos judiciais brasileiros.

Quando o usuário fornecer um processo
do TJRS e solicitar informações sobre ele,
use a ferramenta consultar_processo.

Nunca invente informações processuais.

Responda usando os dados fornecidos
pelas ferramentas.
"""


def create_legal_graph(
    service: SearchService,
):
    tools = create_process_tools(service)

    tools_by_name = {
        tool.name: tool
        for tool in tools
    }

    model = ChatOllama(
        model="qwen3:8b",
        temperature=0,
    )

    model_with_tools = model.bind_tools(
        tools
    )

    async def call_model(
        state: AgentState,
    ):
        response = (
            await model_with_tools.ainvoke(
                [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    *state["messages"],
                ]
            )
        )

        return {
            "messages": [response],
            "llm_calls": (
                state.get(
                    "llm_calls",
                    0,
                )
                + 1
            ),
        }

    def should_continue(
        state: AgentState,
    ) -> Literal[
        "search_process",
        "__end__",
    ]:
        last_message = (
            state["messages"][-1]
        )

        if last_message.tool_calls:
            return "search_process"

        return END

    def has_cached_process(
        state: AgentState,
        requested_npu: str,
    ) -> bool:
        return (
            state.get("npu") == requested_npu
            and state.get("process_data") is not None
        )

    async def search_process(
        state: AgentState,
    ):
        last_message = (
            state["messages"][-1]
        )

        tool_call = (
            last_message.tool_calls[0]
        )

        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        tool_call_id = tool_call["id"]
        requested_npu = tool_args["npu"]

        print(
        f"[GRAPH] Executando tool: {tool_name}"
    )

        
        if has_cached_process(state, requested_npu):
            print(
                f"[CACHE] Reutilizando dados do processo: "
                f"{requested_npu}"
            )

            result = state["process_data"]
            cache_hits = state.get("cache_hits", 0) + 1
            external_calls = state.get("external_calls_count", 0)

        else:
            print(
                f"[TJRS] Consultando processo: "
                f"{requested_npu}"
            )

            tool = tools_by_name[tool_name]

            result = await tool.ainvoke(tool_args)
            cache_hits = state.get("cache_hits", 0)
            external_calls = state.get("external_calls_count", 0) + 1
        return {
            "messages": [
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            ],

            "npu": requested_npu,
            "process_data": result,
            "tool_calls_count": state.get("tool_calls_count", 0) + 1,
            "external_calls_count": external_calls,
            "cache_hits": cache_hits,
        }

    graph_builder = StateGraph(
        AgentState
    )

    graph_builder.add_node(
        "agent",
        call_model,
    )

    graph_builder.add_node(
        "search_process",
        search_process,
    )

    graph_builder.add_edge(
        START,
        "agent",
    )

    graph_builder.add_conditional_edges(
        "agent",
        should_continue,
    )

    graph_builder.add_edge(
        "search_process",
        "agent",
    )

    checkpointer = InMemorySaver()

    return graph_builder.compile(
    checkpointer=checkpointer
)
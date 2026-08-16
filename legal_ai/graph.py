import os

from langchain_ollama import ChatOllama
from langgraph.graph import (
    START,
    StateGraph,
)

from crawler_jus.services.search_service import (
    SearchService,
)
from legal_ai.nodes import (
    call_model,
    prepare_context,
    search_process,
    should_continue,
)
from legal_ai.state import AgentState
from legal_ai.tools import create_process_tools


async def prepare_context_node(
    state: AgentState,
):
    """Adapta prepare_context para a assinatura de node esperada pelo LangGraph.

    Args:
        state (AgentState): Estado atual do grafo.

    Returns:
        dict: Atualização produzida pelo node de preparação de contexto.
    """
    return await prepare_context(state)


def create_legal_graph(
    service: SearchService,
    checkpointer,
    model=None,
):
    """Cria e compila o workflow LangGraph do assistente jurídico.

    Configura modelo, ferramentas, nodes, roteamento condicional e checkpoint de persistência.

    Args:
        service (SearchService): Serviço usado pelas ferramentas processuais.
        checkpointer: Implementação de checkpoint usada para persistir o estado por thread.
        model: Modelo opcional injetado no grafo. Quando omitido, usa ChatOllama com Qwen.

    Returns:
        Grafo LangGraph compilado e pronto para execução.
    """
    tools = create_process_tools(service)

    tools_by_name = {tool.name: tool for tool in tools}
    if model is None:
        model = ChatOllama(
            model="qwen3:8b",
            temperature=0,
            base_url=os.getenv(
                "OLLAMA_BASE_URL",
                "http://localhost:11434",
            ),
        )

    model_with_tools = model.bind_tools(tools)

    async def agent_node(
        state: AgentState,
    ):
        """Adapta a chamada do modelo para a assinatura de node do LangGraph.

        Args:
            state (AgentState): Estado atual do grafo.

        Returns:
            dict: Atualização produzida pela chamada ao modelo.
        """
        return await call_model(
            state,
            model_with_tools,
        )

    async def search_process_node(
        state: AgentState,
    ):
        """Adapta search_process para a assinatura de node do LangGraph.

        Args:
            state (AgentState): Estado atual do grafo.

        Returns:
            dict: Atualização produzida pela execução da ferramenta de consulta.
        """
        return await search_process(
            state,
            tools_by_name,
        )

    graph_builder = StateGraph(AgentState)

    graph_builder.add_node(
        "prepare_context",
        prepare_context_node,
    )

    graph_builder.add_node(
        "agent",
        agent_node,
    )

    graph_builder.add_node(
        "search_process",
        search_process_node,
    )

    graph_builder.add_edge(
        START,
        "prepare_context",
    )

    graph_builder.add_conditional_edges(
        "agent",
        should_continue,
    )

    graph_builder.add_edge(
        "search_process",
        "prepare_context",
    )

    graph_builder.add_edge(
        "prepare_context",
        "agent",
    )

    return graph_builder.compile(checkpointer=checkpointer)

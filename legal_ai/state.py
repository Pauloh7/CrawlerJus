from typing import Annotated, Any, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """Estado compartilhado entre os nodes do agente jurídico.
    
    Armazena histórico de mensagens, NPU atual, dados completos do processo, contexto reduzido, tipo da pergunta, contadores de execução e informações de erro.
    """
    messages: Annotated[list[AnyMessage], add_messages]

    npu: str | None
    process_data: dict[str, Any] | None

    question_type: str | None
    context_data: dict[str, Any] | None

    active_skill: str | None
    skill_instructions: str | None

    llm_calls: int
    tool_calls_count: int
    external_calls_count: int
    cache_hits: int

    error: str | None
    error_type: str | None

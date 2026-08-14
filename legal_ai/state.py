from typing import Annotated,Any, TypedDict

from langchain.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]

    npu: str | None
    process_data: dict[str, Any] | None

    llm_calls: int
    tool_calls_count: int
    external_calls_count: int
    cache_hits: int
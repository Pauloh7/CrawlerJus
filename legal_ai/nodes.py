import logging
import time
from typing import Literal

from langchain.messages import ToolMessage
from langgraph.graph import END

from api.exceptions import TJRSBaseError
from api.request_context import request_id_context
from crawler_jus.util import valida_npu
from legal_ai.skill_loader import load_skill
from legal_ai.skill_selector import (
    select_skill_name,
)
from legal_ai.state import AgentState
from legal_ai.util import (
    classify_question,
    get_last_user_question,
    get_user_npu,
    select_npu,
)

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """
Você é um assistente especializado em processos judiciais brasileiros.

Quando o usuário fornecer um número de processo e solicitar
informações concretas sobre esse processo, use a ferramenta
consultar_processo.

IMPORTANTE:
- Não tente validar, corrigir ou deduzir o formato do NPU por conta própria.
- A validação do NPU é responsabilidade da aplicação.
- Se o usuário fornecer um número de processo, passe esse número
  para a ferramenta consultar_processo.
- Nunca invente números de processo.
- Nunca substitua o número fornecido pelo usuário por outro número.

Se uma ferramenta retornar que o NPU é inválido, informe
ao usuário que o número fornecido é inválido.

Se uma ferramenta retornar erro, não invente uma resposta.
Informe claramente que a consulta não pôde ser concluída.

Nunca invente informações processuais.

Responda usando apenas os dados disponíveis na conversa
ou retornados pelas ferramentas.
"""

async def select_skill(
    state: AgentState,
):
    question = (
        get_last_user_question(state)
        or ""
    )

    skill_name = select_skill_name(
        question
    )

    skill = load_skill(
        skill_name
    )

    logger.info(
        "agent_skill_selected",
        extra={
            "request_id": (
                request_id_context.get()
            ),
            "skill": skill.name,
        },
    )

    return {
        "active_skill": skill.name,
        "skill_instructions": (
            skill.instructions
        ),
    }

def has_cached_process(
    state: AgentState,
    requested_npu: str,
) -> bool:
    """Verifica se o estado já contém dados do NPU solicitado.
    
    Args:
        state (AgentState): Estado atual do agente.
        requested_npu (str): NPU selecionado para a consulta.
    
    Returns:
        bool: True quando o NPU coincide com o estado e process_data está preenchido.
    """
    return state.get("npu") == requested_npu and state.get("process_data") is not None


async def search_process(
    state: AgentState,
    tools_by_name: dict,
):
    """Executa ou reutiliza a consulta de processo solicitada pelo agente.

    Seleciona o NPU por ordem de confiança, valida a ferramenta e o número
    do processo, reutiliza dados do estado quando disponíveis e controla
    contadores de tool, cache e chamadas externas.

    Args:
        state (AgentState): Estado atual do agente.
        tools_by_name (dict): Mapeamento das ferramentas disponíveis pelo nome.

    Returns:
        dict: Atualização parcial do estado com ToolMessage, dados do processo,
        contadores e erros.
    """
    request_id = request_id_context.get()
    started_at = time.perf_counter()

    last_message = state["messages"][-1]
    tool_call = last_message.tool_calls[0]

    tool_name = tool_call["name"]
    tool_args = tool_call["args"]
    tool_call_id = tool_call["id"]

    tool_calls_count = state.get(
        "tool_calls_count",
        0,
    ) + 1

    current_external_calls = state.get(
        "external_calls_count",
        0,
    )

    current_cache_hits = state.get(
        "cache_hits",
        0,
    )

    llm_npu = tool_args.get("npu")
    user_npu = get_user_npu(state)
    state_npu = state.get("npu")

    requested_npu = select_npu(
        user_npu=user_npu,
        state_npu=state_npu,
        llm_npu=llm_npu,
    )

    logger.info(
        "agent_tool_started",
        extra={
            "request_id": request_id,
            "tool": tool_name,
            "npu": requested_npu,
            "tool_call_number": tool_calls_count,
        },
    )

    tool = tools_by_name.get(tool_name)

    if tool is None:
        logger.warning(
            "agent_unknown_tool",
            extra={
                "request_id": request_id,
                "tool": tool_name,
                "tool_call_number": tool_calls_count,
            },
        )

        return {
            "messages": [
                ToolMessage(
                    content=(
                        f"A ferramenta '{tool_name}' "
                        "não está disponível."
                    ),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            ],
            "tool_calls_count": tool_calls_count,
            "error": f"Tool desconhecida: {tool_name}",
            "error_type": "UNKNOWN_TOOL",
        }

    if not requested_npu:
        logger.warning(
            "agent_missing_npu",
            extra={
                "request_id": request_id,
                "tool": tool_name,
                "tool_call_number": tool_calls_count,
            },
        )

        return {
            "messages": [
                ToolMessage(
                    content=(
                        "Nenhum número de processo foi informado."
                    ),
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            ],
            "tool_calls_count": tool_calls_count,
            "error": "NPU não informado",
            "error_type": "MISSING_NPU",
        }

    if not valida_npu(requested_npu):
        logger.warning(
            "agent_invalid_npu",
            extra={
                "request_id": request_id,
                "tool": tool_name,
                "npu": requested_npu,
                "tool_call_number": tool_calls_count,
            },
        )

        return {
            "messages": [
                ToolMessage(
                    content=f"NPU inválido: {requested_npu}",
                    tool_call_id=tool_call_id,
                    name=tool_name,
                )
            ],
            "tool_calls_count": tool_calls_count,
            "error": f"NPU inválido: {requested_npu}",
            "error_type": "INVALID_NPU",
        }

    tool_args["npu"] = requested_npu

    if has_cached_process(
        state,
        requested_npu,
    ):
        result = state["process_data"]

        cache_hits = current_cache_hits + 1
        external_calls = current_external_calls
        source = "checkpoint"

        logger.info(
            "agent_tool_cache_hit",
            extra={
                "request_id": request_id,
                "tool": tool_name,
                "npu": requested_npu,
                "cache_hits": cache_hits,
            },
        )

    else:
        external_calls = current_external_calls + 1
        cache_hits = current_cache_hits
        source = "external"

        logger.info(
            "agent_tool_external_call",
            extra={
                "request_id": request_id,
                "tool": tool_name,
                "npu": requested_npu,
                "external_calls": external_calls,
            },
        )

        try:
            result = await tool.ainvoke(
                tool_args
            )

        except TJRSBaseError as exc:
            duration_ms = (
                time.perf_counter() - started_at
            ) * 1000

            logger.warning(
                "agent_tool_failed",
                extra={
                    "request_id": request_id,
                    "tool": tool_name,
                    "npu": requested_npu,
                    "error_type": type(exc).__name__,
                    "duration_ms": round(
                        duration_ms,
                        2,
                    ),
                },
            )

            return {
                "messages": [
                    ToolMessage(
                        content=(
                            "Não foi possível consultar "
                            "o processo no TJRS."
                        ),
                        tool_call_id=tool_call_id,
                        name=tool_name,
                    )
                ],
                "tool_calls_count": tool_calls_count,
                "external_calls_count": external_calls,
                "cache_hits": cache_hits,
                "error": str(exc),
                "error_type": type(exc).__name__,
            }

    duration_ms = (
        time.perf_counter() - started_at
    ) * 1000

    logger.info(
        "agent_tool_completed",
        extra={
            "request_id": request_id,
            "tool": tool_name,
            "npu": requested_npu,
            "source": source,
            "duration_ms": round(
                duration_ms,
                2,
            ),
            "tool_calls": tool_calls_count,
            "external_calls": external_calls,
            "cache_hits": cache_hits,
        },
    )

    return {
        "messages": [
            ToolMessage(
                content=(
                    "Consulta realizada com sucesso. "
                    "Os dados foram armazenados no estado."
                ),
                tool_call_id=tool_call_id,
                name=tool_name,
            )
        ],
        "npu": requested_npu,
        "process_data": result,
        "tool_calls_count": tool_calls_count,
        "external_calls_count": external_calls,
        "cache_hits": cache_hits,
        "error": None,
        "error_type": None,
    }

async def call_model(
    state: AgentState,
    model_with_tools,
):
    """Invoca o modelo com o prompt de sistema, contexto reduzido e histórico.

    Args:
        state (AgentState): Estado atual do agente.
        model_with_tools: Modelo configurado com as ferramentas disponíveis.

    Returns:
        dict: Atualização do estado com a resposta do modelo
        e contador de chamadas ao LLM.
    """
    request_id = request_id_context.get()
    started_at = time.perf_counter()

    current_llm_calls = state.get("llm_calls", 0)

    logger.info(
        "llm_call_started",
        extra={
            "request_id": request_id,
            "llm_call_number": current_llm_calls + 1,
        },
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        }
    ]

    skill_instructions = state.get(
        "skill_instructions"
    )

    if skill_instructions:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Instruções da skill ativa "
                    f"'{state.get('active_skill')}':\n\n"
                    f"{skill_instructions}"
                ),
            }
        )

    context_data = state.get("context_data")

    if context_data:
        messages.append(
            {
                "role": "system",
                "content": (
                    "Dados processuais disponíveis para "
                    "responder à pergunta atual:\n"
                    f"{context_data}"
                ),
            }
        )

    messages.extend(state["messages"])

    try:
        response = await model_with_tools.ainvoke(
            messages
        )
    except Exception as exc:
        duration_ms = (
            time.perf_counter() - started_at
        ) * 1000

        logger.exception(
            "llm_call_failed",
            extra={
                "request_id": request_id,
                "llm_call_number": current_llm_calls + 1,
                "duration_ms": round(
                    duration_ms,
                    2,
                ),
                "error_type": type(exc).__name__,
            },
        )

        raise

    duration_ms = (
        time.perf_counter() - started_at
    ) * 1000

    logger.info(
        "llm_call_completed",
        extra={
            "request_id": request_id,
            "llm_call_number": current_llm_calls + 1,
            "duration_ms": round(
                duration_ms,
                2,
            ),
            "has_tool_calls": bool(
                getattr(
                    response,
                    "tool_calls",
                    None,
                )
            ),
        },
    )

    return {
        "messages": [response],
        "llm_calls": current_llm_calls + 1,
    }


def should_continue(
    state: AgentState,
) -> Literal[
    "search_process",
    "__end__",
]:
    """Define o próximo passo do grafo após uma resposta do modelo.
    
    Args:
        state (AgentState): Estado atual do agente.
    
    Returns:
        Literal: Nome do node search_process quando houver tool call ou END quando a resposta for final.
    """
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "search_process"

    return END


async def prepare_context(
    state: AgentState,
):
    """Prepara somente os dados processuais relevantes para a pergunta atual.
    
    Mantém o process_data completo no estado e cria context_data reduzido conforme o tipo da pergunta, evitando enviar informações desnecessárias ao modelo.
    
    Args:
        state (AgentState): Estado atual do agente contendo process_data e mensagens.
    
    Returns:
        dict: Tipo da pergunta e contexto processual preparado para o modelo.
    """
    process_data = state.get("process_data")

    if not process_data:
        return {
            "context_data": None,
            "question_type": None,
        }

    question = get_last_user_question(state)

    question_type = classify_question(question or "")

    context_data = {"numeroProcesso": process_data.get("numeroProcesso")}

    if question_type == "classe":
        context_data.update(
            {
                "classeCNJ": process_data.get("classeCNJ"),
                "assuntoCNJ": process_data.get("assuntoCNJ"),
                "nomeClasse": process_data.get("nomeClasse"),
                "nomeNatureza": process_data.get("nomeNatureza"),
            }
        )

    elif question_type == "partes":
        context_data["partes"] = process_data.get(
            "partes",
            [],
        )

    elif question_type == "movimentos":
        movimentos = process_data.get(
            "movimentos",
            [],
        )

        context_data["movimentos"] = movimentos[:5]

    else:
        context_data = process_data

    return {
        "context_data": context_data,
        "question_type": question_type,
    }

from langchain.messages import HumanMessage
import re
from legal_ai.state import AgentState

NPU_IN_TEXT_PATTERN = re.compile(r"\b\d{1,7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}\b")


def get_user_npu(
    state: AgentState,
) -> str | None:
    """Extrai um NPU explicitamente informado na mensagem humana mais recente.
    
    Args:
        state (AgentState): Estado atual do agente com o histórico de mensagens.
    
    Returns:
        str | None: NPU encontrado na última mensagem humana ou None quando ausente.
    """
    for message in reversed(state["messages"]):
        if not isinstance(message, HumanMessage):
            continue

        match = NPU_IN_TEXT_PATTERN.search(str(message.content))

        if match:
            return match.group(0)

        # Para na mensagem humana mais recente.
        break

    return None


def select_npu(
    user_npu: str | None,
    state_npu: str | None,
    llm_npu: str | None,
) -> str | None:
    """Seleciona o NPU usando a ordem de confiança definida pelo agente.
    
    Prioridade: NPU informado pelo usuário, NPU persistido no estado e, por último, NPU sugerido pelo LLM.
    
    Args:
        user_npu (str | None): NPU extraído da mensagem do usuário.
        state_npu (str | None): NPU armazenado no estado da conversa.
        llm_npu (str | None): NPU enviado pelo modelo na chamada da ferramenta.
    
    Returns:
        str | None: NPU selecionado para a consulta.
    """
    if user_npu:
        return user_npu

    if state_npu:
        return state_npu

    return llm_npu


def classify_question(question: str) -> str:
    """Classifica a pergunta para definir o contexto processual necessário.
    
    Args:
        question (str): Pergunta atual do usuário.
    
    Returns:
        str: Tipo da pergunta: classe, partes, movimentos ou geral.
    """
    text = question.lower()

    if any(
        term in text
        for term in (
            "classe",
            "classificação",
            "tipo do processo",
        )
    ):
        return "classe"

    if any(
        term in text
        for term in (
            "parte",
            "partes",
            "exequente",
            "executado",
            "autor",
            "réu",
        )
    ):
        return "partes"

    if any(
        term in text
        for term in (
            "movimentação",
            "movimentações",
            "andamento",
            "andamentos",
            "última movimentação",
            "últimas movimentações",
        )
    ):
        return "movimentos"

    return "geral"


def get_last_user_question(
    state: AgentState,
) -> str | None:
    """Retorna o conteúdo da mensagem humana mais recente.
    
    Args:
        state (AgentState): Estado atual do agente.
    
    Returns:
        str | None: Última pergunta humana ou None quando não houver mensagem do usuário.
    """
    for message in reversed(state["messages"]):
        if isinstance(
            message,
            HumanMessage,
        ):
            return str(message.content)

    return None

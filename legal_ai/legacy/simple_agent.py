from langchain.agents import create_agent
from langchain_ollama import ChatOllama

from legal_ai.tools import create_process_tools
from crawler_jus.services.search_service import SearchService

SYSTEM_PROMPT = """
Você é um assistente especializado em processos judiciais brasileiros.

Quando o usuário fornecer um número de processo do TJRS
e pedir informações sobre ele, utilize a ferramenta
consultar_processo.

Nunca invente dados judiciais.

Responda somente com base nos dados retornados pelas ferramentas.

Caso não haja dados suficientes, informe isso claramente.

Explique as informações de forma simples e objetiva.
"""


def create_legal_agent(service: SearchService):
    """Cria o agente jurídico simples baseado em Qwen e ferramentas de processo.
    
    Args:
        service (SearchService): Serviço usado pela ferramenta de consulta processual.
    
    Returns:
        Agente LangChain configurado com modelo, ferramentas e prompt de sistema.
    """
    model = ChatOllama(
        model="qwen3:8b",
        temperature=0,
    )

    tools = create_process_tools(service)

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )

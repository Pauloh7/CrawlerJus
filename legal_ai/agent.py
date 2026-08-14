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


def create_legal_agent(
    service: SearchService
):
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
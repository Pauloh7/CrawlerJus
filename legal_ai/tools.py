import logging

from langchain.tools import tool

from api.request_context import request_id_context
from crawler_jus.services.search_service import SearchService

logger = logging.getLogger(__name__)


def create_process_tools(service: SearchService):
    """Cria as ferramentas processuais disponibilizadas ao agente jurídico.

    Args:
        service (SearchService): Serviço usado para executar consultas ao TJRS.

    Returns:
        list: Lista de ferramentas LangChain vinculadas ao serviço.
    """

    @tool
    async def consultar_processo(npu: str) -> dict:
        """
        Consulta dados de um processo judicial no TJRS.

        Use esta ferramenta sempre que o usuário fornecer um número
        de processo e solicitar dados concretos desse processo,
        como classe, partes, situação, comarca ou movimentações.

        Não valide ou altere o NPU antes da chamada.
        A aplicação fará a validação.

        Args:
            npu: Número do processo exatamente como informado pelo usuário.

        Returns:
            Dados estruturados do processo.
        """
        logger.info(
            "Consultando processo via AI tool",
            extra={
                "request_id": request_id_context.get(),
                "npu": npu,
                "tool": "consultar_processo",
            },
        )

        return await service.search_npu(npu)

    return [consultar_processo]

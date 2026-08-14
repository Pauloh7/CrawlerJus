from langchain.tools import tool

from crawler_jus.services.search_service import SearchService


def create_process_tools(service: SearchService):

    @tool
    async def consultar_processo(npu: str) -> dict:
        """
        Consulta um processo judicial do TJRS pelo número CNJ/NPU.

        Use esta ferramenta quando o usuário pedir informações
        sobre um processo judicial do Tribunal de Justiça
        do Rio Grande do Sul.

        Retorna dados básicos, partes e movimentações.
        """

        print(
            f"[AI TOOL] consultar_processo: {npu}"
        )

        return await service.search_npu(npu)

    return [consultar_processo]
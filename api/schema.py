import re
import logging
from pydantic import BaseModel, field_validator
from crawler_jus.util import (
    normalize_npu_to_20_digits,
    calc_digito_verificador,
    format_cnj,
)

logger = logging.getLogger(__name__)


class ClienteInput(BaseModel):
    """Schema de entrada da consulta de processo.
    
    Attributes:
        npu (str): Número do processo no padrão CNJ, normalizado e validado antes do uso.
    """
    npu: str

    @field_validator("npu", mode="before")
    @classmethod
    def normalize_and_validate_npu(cls, npu):
        """Normaliza e valida o NPU recebido pela API.
        
        Args:
            npu: Número do processo informado pelo cliente.
        
        Returns:
            str: NPU formatado no padrão CNJ.
        
        Raises:
            ValueError: Quando o valor não é string ou o dígito verificador é inválido.
        """
        if not isinstance(npu, str):
            raise ValueError("NPU deve ser string")

        digits20 = normalize_npu_to_20_digits(npu)  # aceita com ou sem pontuação

        expected_digito_verificador = calc_digito_verificador(digits20)
        given_digito_verificador = digits20[7:9]

        if given_digito_verificador != expected_digito_verificador:
            logger.warning(
                f"Dígito verificador inválido no NPU. Esperado: {expected_digito_verificador}"
            )
            raise ValueError(f"O número não é um numero cnj(NPU) válido)")

        return format_cnj(digits20)


class AskIAInput(BaseModel):
    """Schema de entrada do endpoint de perguntas ao agente jurídico.
    
    Attributes:
        thread_id (str): Identificador da conversa usado pelo checkpoint.
        question (str): Pergunta enviada pelo usuário.
    """
    thread_id: str
    question: str


class AskIAResponse(BaseModel):
    """Schema de resposta do endpoint do agente jurídico.
    
    Inclui a resposta textual, identificação da thread, NPU atual, contadores de execução e informações de erro quando existirem.
    """
    answer: str
    thread_id: str

    npu: str | None = None
    llm_calls: int | None = None
    tool_calls: int | None = None
    external_calls: int | None = None
    cache_hits: int | None = None

    error: str | None = None
    error_type: str | None = None

import re
import logging
from pydantic import BaseModel, field_validator
from crawler_jus.util import normalize_npu_to_20_digits

logger = logging.getLogger(__name__)


def format_cnj(digits: str) -> str:
    # npu = 20 dígitos
    return f"{digits[:7]}-{digits[7:9]}.{digits[9:13]}.{digits[13]}.{digits[14:16]}.{digits[16:20]}"

def calc_digito_verificador(digits: str) -> str:
    """
    Algoritmo CNJ (mod 97):
    - pegue 20 dígitos
    - monte: NNNNNNN + AAAAJTROOOO + "00" (substitui o DV por 00 no final)
    - DV = 98 - (base % 97)
    """
    base = digits[:7] + digits[9:] + "00"
    digito_verificador = 98 - (int(base) % 97)
    return f"{digito_verificador:02d}"

class ClienteInput(BaseModel):
    npu: str

    @field_validator("npu", mode="before")
    @classmethod
    def normalize_and_validate_npu(cls, npu):
        if not isinstance(npu, str):
            raise ValueError("NPU deve ser string")

        digits20 = normalize_npu_to_20_digits(npu)  # aceita com ou sem pontuação


        expected_digito_verificador = calc_digito_verificador(digits20)
        given_digito_verificador = digits20[7:9]

        
        if given_digito_verificador != expected_digito_verificador:
            logger.warning(
            f"Dígito verificador inválido no NPU. Esperado: {expected_digito_verificador}")
            raise ValueError(f"O número não é um numero cnj(NPU) válido)")

        return format_cnj(digits20)
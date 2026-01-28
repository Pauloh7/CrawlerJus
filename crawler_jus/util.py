import re
import httpx
import logging
from api.exceptions import TJRSUpstreamError
from bs4 import BeautifulSoup

logger = logging.getLogger()

def remove_blank_space(txt: str) -> str:
    """Função que remove espaços de um texto
    Args:
    txt (str): Texto que se quer remover espaços
    Returns:
        array (str): Texto com espaços removidos
    """
    array = txt.split()
    return " ".join(array).strip()


def remove_special_characters(texto: str) -> str:
    """Função que remove caracteres especiais
    Args:
    texto (str): Texto que se quer remover caracteres especiais
    Returns:
        texto_corrigido (str): Texto com caracteres especiais removidos
    """
    texto_corrigido = texto
    texto_corrigido = re.sub(
        r"[\\\/,;<>\.\?\/\!\*\-\+\_\=\@\#%:\(\)" "]+", "", texto_corrigido
    )
    texto_corrigido = re.sub(r"\(\)", "", texto_corrigido)
    texto_corrigido = re.sub(r"\s{2,}", " ", texto_corrigido)
    texto_corrigido = re.sub(r"^\s+", "", texto_corrigido)
    texto_corrigido = re.sub(r"\s+$", "", texto_corrigido)
    return texto_corrigido


def extract_comarca(npu: str) -> str:
    """Função que extrai comarca do NPU(número de processo unificado)
    Args:
    npu (str): Npu(número de processo unificado) para extrair comarca
    Returns:
        comarca (str): comarca extraida
    """
    # Zeros a esquerda são removidos pois a requisição exige
    comarca = str(int(npu[-4:]))

    return comarca


def build_url_processo(npu: str, comarca: str) -> str:
    """Função que cria url de acesso aos dados basicos e partes
    Args:
    npu (str): Npu(número de processo unificado) para extrair dados
    comarca (str): Comarca do precesso
    Returns:
        url (str): Url pronta
    """
    return f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaProcesso?numeroProcesso={npu}&codComarca={comarca}"


def build_url_movimento(npu: str, comarca: str) -> str:
    """Função que cria url de acesso aos movimentos do processo
    Args:
    npu (str): Npu(número de processo unificado) para extrair dados
    comarca (str): Comarca do precesso
    Returns:
        url (str): Url pronta
    """
    return f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaMovimentacao?numeroProcesso={npu}&codComarca={comarca}"


async def find_main_js() -> str:
    """
    Função que descobre nome do arquivo main_js do tribunal
    Args:
    Returns:
    full_url (str): retorna url completa do main_js
    """

    url_base = "https://consulta.tjrs.jus.br/consulta-processual/"
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url_base)
        html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    # Busca todos os scripts e filtra pelo que começa com 'main.'
    scripts = [script['src'] for script in soup.find_all('script', src=True)]
    main_script_url = next((s for s in scripts if 'main.' in s), None)

    if main_script_url:
        # Se o caminho for relativo, concatena com a base
        full_url = main_script_url if main_script_url.startswith('http') else url_base + main_script_url
        print(f"Arquivo encontrado: {full_url}")
        return full_url


async def find_obfuscate_and_extract_big_int() -> tuple:
    """
    Função que encontra metodo de obfuscação do secrete e extrai numeros base do calculo
    Args:
    Returns:
    big_ints (tuple): Tupla com os dois numeros do calculo
    """

    main_js_url = await find_main_js()

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(main_js_url)
    
    js_code = response.text
    obfuscate_code = re.search(r"obfuscation\s*\([^)]*\)\s*\{[\s\S]*?BigInt\s*\(\s*\d+\s*\)[\s\S]*?BigInt\s*\(\s*\d+\s*\)", js_code)[0]
    big_ints = re.findall(r"BigInt\s*\(\s*(\d+)\s*\)", obfuscate_code)
    if len(big_ints) < 2:
        logger.error(f"Falha Crítica: A estrutura do JS mudou. Encontrados apenas {len(big_ints)} BigInts.")
        raise TJRSUpstreamError("A lógica de ofuscação do Tribunal mudou e o scraper precisa de atualização manual.")
    print(big_ints)
    return big_ints
    
    import re

def normalize_npu_to_20_digits(npu: str) -> str:
    """
    Aceita NPU com ou sem pontuação e com sequencial sem zeros à esquerda.
    Retorna string com 20 dígitos (padrão CNJ).
    """
    if not isinstance(npu, str):
        raise ValueError("NPU deve ser string")

    digits = re.sub(r"\D+", "", npu)

    # Se já veio completo, ok
    if len(digits) == 20:
        return digits

    # Se veio no formato pontuado, tentamos extrair os blocos
    m = re.match(
        r"^\s*(\d{1,7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})\s*$",
        npu
    )
    if m:
        seq, dv, ano, j, tr, oooo = m.groups()
        seq = seq.zfill(7)  # ✅ completa com zeros à esquerda
        return f"{seq}{dv}{ano}{j}{tr}{oooo}"

    # Caso venha só dígitos mas faltando zeros no começo do sequencial
    # (ex: 19 dígitos ou menos) → completa à esquerda até 20
    if len(digits) < 20:
        return digits.zfill(20)

    raise ValueError("NPU inválido (tamanho inesperado)")

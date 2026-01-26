import re
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup


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
    """Função que extrai comarca do NPU
    Args:
    npu (str): Npu para extrair comarca
    Returns:
        comarca (str): comarca extraida
    """
    # Zeros a esquerda são removidos pois a requisição exige
    comarca = str(int(npu[-4:]))

    return comarca


def build_url_processo(npu: str, comarca: str) -> str:
    """Função que cria url de acesso aos dados basicos e partes
    Args:
    npu (str): Npu para extrair dados
    comarca (str): Comarca do precesso
    Returns:
        url (str): Url pronta
    """
    return f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaProcesso?numeroProcesso={npu}&codComarca={comarca}"


def build_url_movimento(npu: str, comarca: str) -> str:
    """Função que cria url de acesso aos movimentos do processo
    Args:
    npu (str): Npu para extrair dados
    comarca (str): Comarca do precesso
    Returns:
        url (str): Url pronta
    """
    return f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaMovimentacao?numeroProcesso={npu}&codComarca={comarca}"


def valida_npu(npu):
    """
    Função para validar o número do processo judicial utilizando o algoritmo Módulo 97, Base 10, ISO 7064
    Args:
    npu (str): Numero a ser validado
    Returns:
    retorna True se o numero é valido e False se esse é invalido
    """

    npu = npu.replace(".", "").replace("-", "")
    npu_sem_digito_verificador = npu[:7] + npu[9:]

    try:
        digito_verificador = 98 - ((int(npu_sem_digito_verificador) * 100) % 97)
    except:
        return False

    return int(npu[7:9]) == digito_verificador

def find_main_js() -> str:
    """
    Função que descobre nome do arquivo main_js do tribunal
    Args:
    Returns:
    full_url (str): retorna url completa do main_js
    """

    url_base = "https://consulta.tjrs.jus.br/consulta-processual/"
    response = requests.get(url_base)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Busca todos os scripts e filtra pelo que começa com 'main.'
    scripts = [script['src'] for script in soup.find_all('script', src=True)]
    main_script_url = next((s for s in scripts if 'main.' in s), None)

    if main_script_url:
        # Se o caminho for relativo, concatena com a base
        full_url = main_script_url if main_script_url.startswith('http') else url_base + main_script_url
        print(f"Arquivo encontrado: {full_url}")
        return full_url


def find_obfuscate_and_extract_big_int() -> tuple:
    """
    Função que encontra metodo de obfuscação do secrete e extrai numeros base do calculo
    Args:
    Returns:
    big_ints (tuple): Tupla com os dois numeros do calculo
    """

    main_js_url = find_main_js()

    response = requests.get(main_js_url)
    js_code = response.text
    obfuscate_code = re.search(r"obfuscation\s*\([^)]*\)\s*\{[\s\S]*?BigInt\s*\(\s*\d+\s*\)[\s\S]*?BigInt\s*\(\s*\d+\s*\)", js_code)[0]
    big_ints = re.findall(r"BigInt\s*\(\s*(\d+)\s*\)", obfuscate_code)
    print(big_ints)
    return big_ints
    

if __name__ == "__main__":
    find_obfuscate_and_extract_big_int()
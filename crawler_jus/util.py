import re


def remove_blank_space(txt):
    """"""
    array = txt.split()
    return " ".join(array).strip()


def remove_special_characters(texto):
    """"""
    texto_corrigido = texto
    texto_corrigido = re.sub(
        r"[\\\/,;<>\.\?\/\!\*\-\+\_\=\@\#%:\(\)" "]+", "", texto_corrigido
    )
    texto_corrigido = re.sub(r"\(\)", "", texto_corrigido)
    texto_corrigido = re.sub(r"\s{2,}", " ", texto_corrigido)
    texto_corrigido = re.sub(r"^\s+", "", texto_corrigido)
    texto_corrigido = re.sub(r"\s+$", "", texto_corrigido)
    return texto_corrigido

def extract_comarca(npu:str) -> str:
        ''''''
        comarca = str(int(npu[-4:]))

        return comarca

def build_url_processo(npu: str, comarca: str) -> str:
    return f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaProcesso?numeroProcesso={npu}&codComarca={comarca}"

def build_url_movimento(npu: str, comarca: str) -> str:
    return f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaMovimentacao?numeroProcesso={npu}&codComarca={comarca}"

def valida_npu(npu):
    '''
    Função para validar o número do processo judicial utilizando o algoritmo Módulo 97, Base 10, ISO 7064

    Input:
    ------
    numero_processo: string

    Output:
    -------
    retorna True se o numero é valido e False se esse é invalido
    
    '''

    npu = npu.replace('.','').replace('-', '')
    npu_sem_digito_verificador = npu[:7] + npu[9:]

    try:
        digito_verificador = 98 - ((int(npu_sem_digito_verificador) * 100) % 97)
    except:
        return False

    return int(npu[7:9]) == digito_verificador
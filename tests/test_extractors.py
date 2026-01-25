import json
from crawler_jus.crawler import Crawler

def test_extract_basic_data_partes():
    crawler = Crawler()
    payload = {
  "data": [
    {
      "movimentos": {
        "movimento": [
          {
            "data": "15/01/2026",
            "descricao": "Conclusos para decisão/despacho",
            "conclusaoAoJuiz": "null",
            "documentos": [],
            "codDocumento": "null",
            "numero": 2,
            "codMovimentoCNJ": "null",
            "julgadores": "null",
            "numeroProcessoCNJ": "null",
            "protocolo": "null",
            "complemento": "null"
          },
          {
            "data": "15/01/2026",
            "descricao": "Distribuído por dependência (CAN2CIV1J) - Número: 50019831220138210008/RS",
            "conclusaoAoJuiz": "null",
            "documentos": [],
            "codDocumento": "null",
            "numero": 1,
            "codMovimentoCNJ": "null",
            "julgadores": "null",
            "numeroProcessoCNJ": "null",
            "protocolo": "null",
            "complemento": "null"
          }
        ]
      },
      "partes": {
        "parte": [
          {
            "advogados": {
              "advogado": [
                {
                  "nome": "null",
                  "oab": "null"
                }
              ]
            },
            "descricaoTipo": "EXEQUENTE",
            "nome": "UNIFERTIL - UNIVERSAL DE FERTILIZANTES S/A"
          },
          {
            "advogados": {
              "advogado": [
                {
                  "nome": "null",
                  "oab": "null"
                }
              ]
            },
            "descricaoTipo": "EXECUTADO",
            "nome": "BANCO BRADESCO S.A."
          },
          {
            "advogados": {
              "advogado": [
                {
                  "nome": "null",
                  "oab": "null"
                }
              ]
            },
            "descricaoTipo": "EXECUTADO",
            "nome": "PETRÓLEO BRASILEIRO S/A - PETROBRÁS"
          }
        ]
      },
      "localAutosEletronicos": "null",
      "assuntoCNJ": "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL",
      "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
      "codigoComarca": "8",
      "comarca": {
        "codigo": "8",
        "nome": "CANOAS"
      },
      "dataDistribuicao": "15/01/2026 09:31:53",
      "folhas": "null",
      "indTipoProcesso": "E",
      "numero": "null",
      "numeroCNJ": "50016466620268210008",
      "numeroCNJFormatado": "5001646-66.2026.8.21.0008",
      "numeroFormatado": "null",
      "orgaoJulgador": {
        "nome": "1º Juízo da 2ª Vara Cível da Comarca de Canoas",
        "julgador": {
          "nome": "null"
        }
      },
      "segredoJustica": "false",
      "situacao": "null",
      "tipoProcesso": "EPROC",
      "volumes": "null",
      "numeroAntigo": "null",
      "dataPropositura": "null",
      "nomeSecao": "null",
      "nomeClasse": "CUMPRIMENTO DE SENTENÇA",
      "nomeNatureza": "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL",
      "situacaoProcesso": "MOVIMENTO-AGUARDA DESPACHO",
      "reuIdoso": "N",
      "classe": "null",
      "natureza": {
        "codigo": "02190310",
        "nome": "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL",
        "naturezaThemis": "null"
      },
      "numeroProcessoPrincipal": "null",
      "processoOrigem": {
        "numeroProcessoOrigem": "50019831220138210008",
        "codigoComarcaOrigem": "null",
        "municipioOrigem": "null",
        "varaOrigem": "null"
      },
      "processosVinculados": [
        {
          "codigoComarca": "0008",
          "numeroCNJ": "50019831220138210008",
          "depositosJudiciais": [],
          "leiloesPracas": [],
          "alvaras": [],
          "guias": [],
          "processosDeprecados": [],
          "movimentos": [],
          "partes": [],
          "audiencias": [],
          "termosAudiencias": [],
          "sentencas": [],
          "despachos": [],
          "processosVinculados": [],
          "notas": [],
          "mandados": [],
          "outrosParametros": []
        }
      ]
    }
  ],
  "exceptionKey": 0,
  "messages": "null",
  "uri": "null"
}
    basic_data_partes = crawler.extract_basic_data_partes(json.dumps(payload))
    assert basic_data_partes["nomeClasse"] == "CUMPRIMENTO DE SENTENÇA"
    assert basic_data_partes["nomeNatureza"] == "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL"
    assert basic_data_partes["classeCNJ"] == "CUMPRIMENTO DE SENTENÇA"
    assert basic_data_partes["assuntoCNJ"] == "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL"
    assert len(basic_data_partes["partes"]) == 3

def test_extract_movimentos():
    crawler = Crawler()
    payload = {
  "data": [
    {
      "codMovimentoCNJ": "null",
      "data": "23/01/2026",
      "descricao": "Expedida/certificada a intimação eletrônica - Despacho/Decisão (EXEQUENTE -  PETRÓLEO BRASILEIRO S/A - PETROBRÁS)  Prazo: 15 dias",
      "ultimaAtualizacao": "25/01/2026 15:44",
      "conclusaoAoJuiz": "null",
      "documentos": [],
      "codDocumento": "null",
      "numero": 4,
      "julgadores": "null",
      "numeroProcessoCNJ": "null",
      "protocolo": "null",
      "complemento": "null"
    },
    {
      "codMovimentoCNJ": "null",
      "data": "23/01/2026",
      "descricao": "Proferido despacho de mero expediente",
      "ultimaAtualizacao": "25/01/2026 15:44",
      "conclusaoAoJuiz": "null",
      "documentos": [
        {
          "seqDocumento": 1,
          "desDocumento": "DESPACHO/DECISÃO",
          "linkDocumento": "https://eproc1g.tjrs.jus.br/eproc/controlador.php?acao=acessar_documento_publico&doc=11769193216782443884294546860&evento=82100006&key=acba50c5b1f4506af906e808ff9b9c83deb5e23c506c00fc09f24e6c04658138&hash=d54f9f31b928ae84ab56cc6ea032f431"
        }
      ],
      "codDocumento": "null",
      "numero": 3,
      "julgadores": "null",
      "numeroProcessoCNJ": "null",
      "protocolo": "null",
      "complemento": "null"
    },
    {
      "codMovimentoCNJ": "null",
      "data": "15/01/2026",
      "descricao": "Conclusos para decisão/despacho",
      "ultimaAtualizacao": "25/01/2026 15:44",
      "conclusaoAoJuiz": "null",
      "documentos": [],
      "codDocumento": "null",
      "numero": 2,
      "julgadores": "null",
      "numeroProcessoCNJ": "null",
      "protocolo": "null",
      "complemento": "null"
    },
    {
      "codMovimentoCNJ": "null",
      "data": "14/01/2026",
      "descricao": "Distribuído por dependência (CAN1CIV2J) - Número: 50035062520148210008/RS",
      "ultimaAtualizacao": "25/01/2026 15:44",
      "conclusaoAoJuiz": "null",
      "documentos": [],
      "codDocumento": "null",
      "numero": 1,
      "julgadores": "null",
      "numeroProcessoCNJ": "null",
      "protocolo": "null",
      "complemento": "null"
    }
  ],
  "exceptionKey": 0,
  "messages": "null",
  "uri": "null"
}
    movimentos = crawler.extract_movimentos(json.dumps(payload))
    assert len(movimentos) == 4
    assert movimentos[0]["data"] == "23/01/2026"
    assert movimentos[0]["descricao"].startswith("Expedida/certificada a intimação eletrônica")

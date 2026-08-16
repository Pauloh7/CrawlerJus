import json

import pytest
from langchain.messages import HumanMessage

from legal_ai.nodes import prepare_context


@pytest.mark.asyncio
async def test_prepare_context_deve_selecionar_classe():
    state = {
        "messages": [HumanMessage(content="Qual é a classe do processo?")],
        "process_data": {
            "numeroProcesso": "5001646-66.2026.8.21.0008",
            "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
            "assuntoCNJ": "DIREITO CIVIL",
            "partes": [{"nome": "UNIFERTIL"}],
            "movimentos": [{"descricao": "Intimação"}],
        },
    }

    result = await prepare_context(state)

    assert result["question_type"] == "classe"

    assert result["context_data"]["classeCNJ"] == "CUMPRIMENTO DE SENTENÇA"

    assert "partes" not in result["context_data"]
    assert "movimentos" not in result["context_data"]


@pytest.mark.asyncio
async def test_prepare_context_partes_nao_deve_incluir_movimentos():
    state = {
        "messages": [HumanMessage(content="Quais são as partes do processo?")],
        "process_data": {
            "numeroProcesso": "5001646-66.2026.8.21.0008",
            "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
            "assuntoCNJ": "DIREITO CIVIL",
            "partes": [
                {
                    "descricaoTipo": "EXEQUENTE",
                    "nome": "UNIFERTIL",
                }
            ],
            "movimentos": [
                {
                    "data": "03/08/2026",
                    "descricao": "Publicado no DJEN",
                }
            ],
        },
    }

    result = await prepare_context(state)

    assert result["question_type"] == "partes"
    assert "partes" in result["context_data"]
    assert "movimentos" not in result["context_data"]
    assert "classeCNJ" not in result["context_data"]


@pytest.mark.asyncio
async def test_prepare_context_movimentos_deve_limitar_quantidade():
    movimentos = [
        {
            "data": f"0{i}/08/2026",
            "descricao": f"Movimento {i}",
        }
        for i in range(1, 11)
    ]

    state = {
        "messages": [HumanMessage(content="Quais foram as últimas movimentações?")],
        "process_data": {
            "numeroProcesso": "5001646-66.2026.8.21.0008",
            "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
            "partes": [],
            "movimentos": movimentos,
        },
    }

    result = await prepare_context(state)

    assert result["question_type"] == "movimentos"

    assert len(result["context_data"]["movimentos"]) == 5

    assert "partes" not in result["context_data"]
    assert "classeCNJ" not in result["context_data"]


@pytest.mark.asyncio
async def test_prepare_context_geral_deve_manter_process_data():
    process_data = {
        "numeroProcesso": "5001646-66.2026.8.21.0008",
        "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
        "partes": [],
        "movimentos": [],
    }

    state = {
        "messages": [HumanMessage(content="Me explique o processo.")],
        "process_data": process_data,
    }

    result = await prepare_context(state)

    assert result["question_type"] == "geral"
    assert result["context_data"] == process_data





@pytest.mark.asyncio
async def test_prepare_context_deve_reduzir_tamanho_do_contexto():
    process_data = {
        "numeroProcesso": "5001646-66.2026.8.21.0008",
        "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
        "assuntoCNJ": "DIREITO CIVIL",
        "partes": [
            {
                "descricaoTipo": "EXEQUENTE",
                "nome": "UNIFERTIL",
            },
            {
                "descricaoTipo": "EXECUTADO",
                "nome": "BANCO BRADESCO",
            },
        ],
        "movimentos": [
            {
                "data": f"{i:02d}/08/2026",
                "descricao": f"Movimento processual {i}",
            }
            for i in range(1, 30)
        ],
    }

    state = {
        "messages": [HumanMessage(content="Qual é a classe do processo?")],
        "process_data": process_data,
    }

    result = await prepare_context(state)

    full_context = json.dumps(
        process_data,
        ensure_ascii=False,
    )

    reduced_context = json.dumps(
        result["context_data"],
        ensure_ascii=False,
    )

    assert len(reduced_context) < len(full_context)
    reduction_ratio = 1 - len(reduced_context) / len(full_context)

    assert reduction_ratio > 0.5

    print(f"Full context: {len(full_context)} chars")

    print(f"Reduced context: {len(reduced_context)} chars")

    print(f"Reduction: {reduction_ratio:.2%}")

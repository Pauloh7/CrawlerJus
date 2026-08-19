import pytest
from langchain.messages import HumanMessage

from legal_ai.nodes import select_skill
from legal_ai.skill_loader import (
    discover_skills,
    load_skill,
)
from legal_ai.skill_selector import (
    select_skill_name,
)


@pytest.mark.asyncio
async def test_select_skill_node():
    state = {
        "messages": [
            HumanMessage(
                content=(
                    "Resuma o processo."
                )
            )
        ]
    }

    result = await select_skill(
        state
    )

    assert (
        result["active_skill"]
        == "resumo-processual"
    )

    assert result[
        "skill_instructions"
    ]


def test_discover_skills():
    skills = discover_skills()

    assert "consulta-processual" in skills
    assert "resumo-processual" in skills
    assert "movimentos-processuais" in skills


def test_load_skill():
    skill = load_skill(
        "consulta-processual"
    )

    assert (
        skill.name
        == "consulta-processual"
    )

    assert (
        "consultar_processo"
        in skill.instructions
    )


def test_select_skill_consulta():
    result = select_skill_name(
        "Qual é a classe do processo?"
    )

    assert (
        result
        == "consulta-processual"
    )


def test_select_skill_resumo():
    result = select_skill_name(
        "Resuma esse processo."
    )

    assert (
        result
        == "resumo-processual"
    )


def test_select_skill_movimentos():
    result = select_skill_name(
        "Quais são as últimas movimentações?"
    )

    assert (
        result
        == "movimentos-processuais"
    )
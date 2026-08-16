from langchain.messages import (
    AIMessage,
    HumanMessage,
)

from legal_ai.util import get_user_npu, classify_question


def test_deve_extrair_npu_da_ultima_mensagem_humana():
    state = {
        "messages": [
            HumanMessage(
                content=(
                    "Consulte o processo "
                    "5001646-66.2026.8.21.0008 "
                    "e me diga a classe."
                )
            )
        ]
    }

    result = get_user_npu(state)

    assert result == "5001646-66.2026.8.21.0008"


def test_nao_deve_usar_npu_de_mensagem_da_ia():
    state = {
        "messages": [
            HumanMessage(content="Quais são as partes dele?"),
            AIMessage(content=("Talvez seja o processo " "5001646-66.2026.8.21.0008")),
        ]
    }

    result = get_user_npu(state)

    assert result is None


def test_deve_considerar_apenas_ultima_mensagem_humana():
    state = {
        "messages": [
            HumanMessage(content=("Consulte " "5001646-66.2026.8.21.0008")),
            AIMessage(content="Ok."),
            HumanMessage(content="E quais são as partes dele?"),
        ]
    }

    result = get_user_npu(state)

    assert result is None


def test_classify_question_classe():
    result = classify_question("Qual é a classe do processo?")

    assert result == "classe"


def test_classify_question_partes():
    result = classify_question("Quais são as partes do processo?")

    assert result == "partes"


def test_classify_question_movimentos():
    result = classify_question("Quais foram as últimas movimentações?")

    assert result == "movimentos"


def test_classify_question_geral():
    result = classify_question("Me explique esse processo.")

    assert result == "geral"

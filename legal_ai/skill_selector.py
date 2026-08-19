from legal_ai.util import classify_question

SUMMARY_TERMS = (
    "resumo",
    "resuma",
    "resumir",
    "síntese",
    "sintese",
    "visão geral",
    "visao geral",
)


def select_skill_name(
    question: str,
) -> str:
    text = question.lower()

    if any(
        term in text
        for term in SUMMARY_TERMS
    ):
        return "resumo-processual"

    question_type = classify_question(
        question
    )

    if question_type == "movimentos":
        return "movimentos-processuais"

    return "consulta-processual"
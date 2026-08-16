NPU = "5001646-66.2026.8.21.0008"


EVAL_CASES = [
    {
        "id": "classe_processo",
        "question": (
            f"Consulte o processo {NPU} "
            "e me diga qual é a classe."
        ),
        "expected_npu": NPU,
        "answer_contains": [
            "CUMPRIMENTO DE SENTENÇA",
        ],
        "max_external_calls": 1,
        "expected_tool_calls": 1,
    },
    {
        "id": "pergunta_conceitual",
        "question": (
            "O que significa conclusão para decisão?"
        ),
        "expected_npu": None,
        "answer_contains": [],
        "max_external_calls": 0,
        "expected_tool_calls": 0,
    },
    {
        "id": "sem_contexto_nao_inventa_npu",
        "question": (
            "Quais são as partes dele?"
        ),
        "expected_npu": None,
        "answer_contains": [],
        "max_external_calls": 0,
        "expected_tool_calls": 0,
    },
    {
        "id": "npu_invalido",
        "question": (
            "Consulte o processo 123 "
            "e me diga qual é a classe."
        ),
        "expected_npu": None,
        "answer_contains": [
            "INVÁLIDO",
        ],
        "max_external_calls": 0,
        "expected_tool_calls": 1,
    },
    {
        "id": "movimentacoes_processo",
        "question": (
            f"Consulte o processo {NPU} "
            "e me diga as últimas movimentações."
        ),
        "expected_npu": NPU,
        "answer_contains": [],
        "max_external_calls": 1,
        "expected_tool_calls": 1,
    },
    {
        "id": "resumo_geral_processo",
        "question": (
            f"Consulte o processo {NPU} "
            "e me dê um resumo geral."
        ),
        "expected_npu": NPU,
        "answer_contains": [
            "CUMPRIMENTO DE SENTENÇA",
        ],
        "max_external_calls": 1,
        "expected_tool_calls": 1,
    },
]
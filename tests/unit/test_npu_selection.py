from legal_ai.util import select_npu

NPU_A = "5001646-66.2026.8.21.0008"
NPU_B = "5001983-12.2013.8.21.0008"
NPU_LLM = "1022402-24.2020.1.01.0101"


def test_user_npu_deve_ter_prioridade():
    result = select_npu(
        user_npu=NPU_A,
        state_npu=NPU_B,
        llm_npu=NPU_LLM,
    )

    assert result == NPU_A


def test_state_npu_deve_ser_usado_sem_npu_do_usuario():
    result = select_npu(
        user_npu=None,
        state_npu=NPU_A,
        llm_npu=NPU_LLM,
    )

    assert result == NPU_A


def test_llm_npu_deve_ser_ultimo_recurso():
    result = select_npu(
        user_npu=None,
        state_npu=None,
        llm_npu=NPU_A,
    )

    assert result == NPU_A


def test_sem_npu_deve_retornar_none():
    result = select_npu(
        user_npu=None,
        state_npu=None,
        llm_npu=None,
    )

    assert result is None

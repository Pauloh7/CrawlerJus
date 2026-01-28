from crawler_jus.util import (
    remove_special_characters,
    extract_comarca,
    build_url_processo,
    build_url_movimento,
)


def test_remove_special_characters():
    assert (
        remove_special_characters("5001646-66.2026.8.21.0008") == "50016466620268210008"
    )


def test_extract_comarca():
    assert extract_comarca("50016466620268210008") == "8"


def test_build_urls():
    npu = "50016466620268210008"
    comarca = "8"
    assert (
        f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaProcesso?numeroProcesso={npu}&codComarca={comarca}"
        in build_url_processo(npu, comarca)
    )
    assert (
        f"https://consulta-processual-service.tjrs.jus.br/api/consulta-service/v1/consultaMovimentacao?numeroProcesso={npu}&codComarca={comarca}"
        in build_url_movimento(npu, comarca)
    )



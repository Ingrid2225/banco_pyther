
import pytest
import httpx
from fastapi import HTTPException


from clientes_api.app.routers.contas import get_db, _raise_unavailable, _safe_detail
from clientes_api.app.services.db_conta import DbConta


def _http_status_error_with_detail(detail, status=500):
    req = httpx.Request("GET", "http://x")
    resp = httpx.Response(status, json={"detail": detail})
    return httpx.HTTPStatusError("err", request=req, response=resp)


def test_get_db_usa_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("CLIENTES_DB_URL", "http://example:1234/")
    db = get_db()
    assert isinstance(db, DbConta)
    # rstrip('/') é aplicado no DbConta, então garantimos que veio sem a barra do final:
    assert db.base_url == "http://example:1234"


def test_raise_unavailable_gera_http_503():
    with pytest.raises(HTTPException) as exc:
        _raise_unavailable()
    err = exc.value
    assert err.status_code == 503
    assert err.detail["code"] == "CLIENTES_DB_INDISPONIVEL"


def test_safe_detail_branch_detail_tipo_lista_vai_para_mensagem_padrao():
   
    e = _http_status_error_with_detail(detail=["algo"], status=502)
    out = _safe_detail(e)
    assert out["status"] == 502
    assert out["code"] == "ERRO_CLIENTES_DB"
    assert "Erro no serviço clientes_db" in out["message"]

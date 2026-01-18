
import pytest
import httpx

from clientes_api.app.routers.contas import get_db, _safe_detail
from clientes_api.app.services.db_conta import DbConta

def _http_status_error(status: int, detail):
    req = httpx.Request("GET", "http://x")
    resp = httpx.Response(status, json={"detail": detail})
    return httpx.HTTPStatusError("err", request=req, response=resp)


def test_get_db_url_padrao_sem_variavel(monkeypatch):
    monkeypatch.delenv("CLIENTES_DB_URL", raising=False)
    db = get_db()
    assert isinstance(db, DbConta)
    assert db.base_url == "http://localhost:8001"


def test_safe_detail_quando_detail_none_vai_para_fallback():
    e = _http_status_error(502, None)
    out = _safe_detail(e)
    assert out["status"] == 502
    assert out["code"] == "ERRO_CLIENTES_DB"
    assert "Erro no serviço clientes_db" in out["message"]


def test_safe_detail_quando_detail_string():
    e = _http_status_error(400, "bad upstream")
    out = _safe_detail(e)
    assert out["status"] == 400
    assert out["code"] == "ERRO_CLIENTES_DB"
    assert out["message"] == "bad upstream"


@pytest.mark.asyncio
async def test_delete_desativar_requesterror_no_obter(api_async_client):
    client, fake = api_async_client

    async def boom_obter(ag, num):
        raise httpx.RequestError("unavailable", request=httpx.Request("GET", "http://x"))
    fake.obter_conta = boom_obter

    r = await client.delete("/contas/111/2222/desativar")
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "CLIENTES_DB_INDISPONIVEL"


@pytest.mark.asyncio
async def test_score_credito_zero(api_async_client):
    client, fake = api_async_client

    async def obter_zero(ag, num):
        return {"saldo_cc": 0.0}
    fake.obter_conta = obter_zero

    r = await client.get("/contas/1/1/score_credito")
    assert r.status_code == 200
    data = r.json()
    assert data["agencia"] == "1"
    assert data["numero_conta"] == "1"
    assert data["score_credito"] == 0.0


@pytest.mark.asyncio
async def test_desativar_primeiro_try_requesterror(api_async_client):
    client, fake = api_async_client

    # 1º try: obter_conta -> RequestError (mapa 503)
    async def boom_obter(ag, num):
        raise httpx.RequestError("unavailable", request=httpx.Request("GET", "http://x"))
    fake.obter_conta = boom_obter

    r = await client.delete("/contas/321/6543/desativar")
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "CLIENTES_DB_INDISPONIVEL"

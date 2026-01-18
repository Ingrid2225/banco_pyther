
import pytest
import httpx
from clientes_api.app.services.db_conta import DbConta

class _FakeResp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "err", request=httpx.Request("GET", "http://x"),
                response=httpx.Response(self.status_code)
            )

    def json(self):
        return self._payload

class _StubAsyncClient:
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc, tb): pass

    async def post(self, url, json=None, timeout=None):
        if url.endswith("/contas"):
            return _FakeResp(201, {**(json or {}), "ok": "criar"})
        if url.endswith("/contas/operacoes/depositar"):
            return _FakeResp(200, {**(json or {}), "ok": "depositar"})
        if url.endswith("/contas/operacoes/sacar"):
            return _FakeResp(200, {**(json or {}), "ok": "sacar"})
        return _FakeResp(200, {**(json or {}), "ok": "post"})

    async def get(self, url, timeout=None):
        if url.endswith("/contas"):
            return _FakeResp(200, [{"agencia": "1234", "numero_conta": "5678"}])
        return _FakeResp(200, {"agencia": "1234", "numero_conta": "5678"})

    async def put(self, url, json=None, timeout=None):
        if "/cheque_especial/cadastrar" in url:
            return _FakeResp(200, {**(json or {}), "ok": "cheque"})
        return _FakeResp(200, {**(json or {}), "ok": "atualizar"})

    async def delete(self, url, timeout=None):
        return _FakeResp(204, None)

@pytest.mark.asyncio
async def test_db_conta_metodos_sucesso(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _StubAsyncClient)

    db = DbConta(base_url="http://fake:8001")

    out = await db.criar_conta({"agencia": "1234", "numero_conta": "5678"})
    assert out["ok"] == "criar"

    out = await db.listar_contas()
    assert isinstance(out, list) and out[0]["agencia"] == "1234"

    out = await db.obter_conta("1234", "5678")
    assert out["numero_conta"] == "5678"

    out = await db.atualizar_conta("1234", "5678", {"nome": "X"})
    assert out["ok"] == "atualizar"

    out = await db.desativar_conta("1234", "5678")
    assert out is None

    out = await db.depositar({"agencia": "1234", "numero_conta": "5678"})
    assert out["ok"] == "depositar"

    out = await db.sacar({"agencia": "1234", "numero_conta": "5678"})
    assert out["ok"] == "sacar"

    out = await db.cadastrar_cheque_especial(1, {"limite": 100, "habilitado": True, "agencia":"1234", "numero_conta":"5678"})
    assert out["ok"] == "cheque"

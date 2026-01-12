
import os, sys, json, builtins
import pytest
import httpx
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clientes_api.app.main import app
from clientes_api.app.routers.clientes import get_db
from clientes_api.app.services.db_client import DbClient


def http_status_error(status: int, detail: str | None = None, method="GET", url="http://fake.local/x"):
    body = {} if detail is None else {"detail": detail}
    content = json.dumps(body).encode("utf-8")
    req = httpx.Request(method, url)
    resp = httpx.Response(status, content=content, headers={"Content-Type": "application/json"}, request=req)
    return httpx.HTTPStatusError("err", request=req, response=resp)

def http_status_error_bad_json(status: int, method="GET", url="http://fake.local/x"):
    req = httpx.Request(method, url)
    resp = httpx.Response(status, content=b"<<bad>>", headers={"Content-Type": "application/json"}, request=req)
    return httpx.HTTPStatusError("err", request=req, response=resp)

def request_error(msg="net"):
    req = httpx.Request("GET", "http://fake.local/x")
    return httpx.RequestError(msg, request=req)

class FakeDbClient:
    def __init__(self):
        self.data = {}
        self.pk = 1

    def reset(self):
        self.data.clear()
        self.pk = 1

    async def create_cliente(self, payload: dict):
        cid = self.pk; self.pk += 1
        item = {"id": cid, **payload}
        self.data[cid] = item
        return item

    async def get_cliente(self, id_: int):
        if id_ not in self.data:
            raise http_status_error(404, "Cliente não encontrado", method="GET", url=f"http://fake-db/clientes/{id_}")
        return self.data[id_]

    async def list_clientes(self):
        return list(self.data.values())

    async def update_cliente(self, id_: int, payload: dict):
        if id_ not in self.data:
            raise http_status_error(404, "Cliente não encontrado", method="PUT", url=f"http://fake-db/clientes/{id_}")
        if "saldo_cc" in payload and payload["saldo_cc"] is not None and float(payload["saldo_cc"]) < 0:
            raise http_status_error(400, "Saldo não pode ser negativo no update.", method="PUT", url=f"http://fake-db/clientes/{id_}")
        self.data[id_].update(payload)
        return self.data[id_]

    async def delete_cliente(self, id_: int):
        if id_ not in self.data:
            raise http_status_error(404, "Cliente não encontrado", method="DELETE", url=f"http://fake-db/clientes/{id_}")
        del self.data[id_]
        return None


@pytest.fixture()
def client_env():
    fake_db = FakeDbClient()
    app.dependency_overrides[get_db] = lambda: fake_db
    with TestClient(app) as client:
        yield client, fake_db
    app.dependency_overrides.clear()
    fake_db.reset()

def test_get_db_env(monkeypatch):
    monkeypatch.delenv("CLIENTES_DB_URL", raising=False)
    assert isinstance(get_db(), DbClient)
    monkeypatch.setenv("CLIENTES_DB_URL", "http://clientes-db:8001")
    assert isinstance(get_db(), DbClient)

def test_create_ok_saldo_explicit(client_env):
    client, _ = client_env
    r = client.post("/clientes", json={"nome": "Maria", "telefone": 11999999999, "correntista": True, "saldo_cc": 100.0})
    assert r.status_code == 201
    assert r.json()["score_credito"] == 0.0
    assert r.json()["saldo_cc"] == 100.0

def test_create_ok_saldo_none_usa_zero(client_env):
    client, _ = client_env
    r = client.post("/clientes", json={"nome": "Zero", "telefone": 110, "correntista": True})
    assert r.status_code == 201
    assert r.json()["score_credito"] == 0.0
    assert r.json()["saldo_cc"] == 0.0

def test_create_negativo_422(client_env):
    client, _ = client_env
    r = client.post("/clientes", json={"nome": "Joao", "telefone": 11988888888, "correntista": False, "saldo_cc": -1.0})
    assert r.status_code == 422
    assert r.json()["detail"] == "cliente inválido, não pode criar conta com saldo negativo"

def test_create_422_bad_json_usa_mensagem_padrao(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(payload): raise http_status_error_bad_json(422, method="POST", url="http://fake-db/clientes")
    monkeypatch.setattr(fake_db, "create_cliente", boom)
    r = client.post("/clientes", json={"nome":"X","telefone":111,"correntista":True,"saldo_cc":1.0})
    assert r.status_code == 422
    assert r.json()["detail"] == "cliente inválido, não pode criar conta com saldo negativo"

def test_create_422_propaga_detail(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(payload): raise http_status_error(422, "saldo interno inválido", method="POST", url="http://fake-db/clientes")
    monkeypatch.setattr(fake_db, "create_cliente", boom)
    r = client.post("/clientes", json={"nome":"Y","telefone":222,"correntista":True,"saldo_cc":2.0})
    assert r.status_code == 422
    assert r.json()["detail"] == "saldo interno inválido"

def test_create_502_bad_json(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(payload): raise http_status_error_bad_json(500, method="POST", url="http://fake-db/clientes")
    monkeypatch.setattr(fake_db, "create_cliente", boom)
    r = client.post("/clientes", json={"nome":"Carlos","telefone":333,"correntista":False,"saldo_cc":10.0})
    assert r.status_code == 502
    assert r.json()["detail"] == "Erro no serviço clientes_db"

def test_create_503_request_error(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(payload): raise request_error("timeout")
    monkeypatch.setattr(fake_db, "create_cliente", boom)
    r = client.post("/clientes", json={"nome":"Paula","telefone":444,"correntista":False,"saldo_cc":200.0})
    assert r.status_code == 503
    assert r.json()["detail"] == "clientes_db indisponível"

def test_create_payload_dict_branch_forcado_por_hasattr_false(client_env, monkeypatch):

    client, _ = client_env

    original_hasattr = builtins.hasattr

    def fake_hasattr(obj, name):
        from clientes_api.app.schemas import ClienteCreate
        if isinstance(obj, ClienteCreate) and name == "model_dump":
            return False
        return original_hasattr(obj, name)

    monkeypatch.setattr(builtins, "hasattr", fake_hasattr)

    r = client.post("/clientes", json={"nome": "SemModelDump", "telefone": 555, "correntista": True, "saldo_cc": 12.0})
    assert r.status_code == 201
    assert r.json()["saldo_cc"] == 12.0
    assert r.json()["score_credito"] == 0.0

def test_create_conversoes_retorno_dict_model_dump_dict_fallback(client_env, monkeypatch):

    client, fake_db = client_env


    async def ret_dict(payload): return {"id": 1, **payload}
    monkeypatch.setattr(fake_db, "create_cliente", ret_dict)
    r1 = client.post("/clientes", json={"nome": "D1", "telefone": 101, "correntista": True, "saldo_cc": 1.0})
    assert r1.status_code == 201
    assert r1.json()["score_credito"] == 0.0


    class ObjV2:
        def __init__(self, d): self._d = d
        def model_dump(self): return dict(self._d)
    async def ret_v2(payload): return ObjV2({"id": 2, **payload})
    monkeypatch.setattr(fake_db, "create_cliente", ret_v2)
    r2 = client.post("/clientes", json={"nome": "D2", "telefone": 102, "correntista": True, "saldo_cc": 2.0})
    assert r2.status_code == 201
    assert r2.json()["id"] == 2


    class ObjV1:
        def __init__(self, d): self._d = d
        def dict(self): return dict(self._d)
    async def ret_v1(payload): return ObjV1({"id": 3, **payload})
    monkeypatch.setattr(fake_db, "create_cliente", ret_v1)
    r3 = client.post("/clientes", json={"nome": "D3", "telefone": 103, "correntista": True, "saldo_cc": 3.0})
    assert r3.status_code == 201
    assert r3.json()["id"] == 3


    class IterablePairs:
        def __iter__(self):
            yield ("id", 999)
            yield ("nome", "Iterável")
            yield ("telefone", 11900000000)
            yield ("correntista", True)
            yield ("saldo_cc", 7.0)
    async def ret_fallback(payload): return IterablePairs()
    monkeypatch.setattr(fake_db, "create_cliente", ret_fallback)
    r4 = client.post("/clientes", json={"nome": "D4", "telefone": 104, "correntista": True, "saldo_cc": 4.0})
    assert r4.status_code == 201
    assert r4.json()["id"] == 999


def test_get_ok(client_env):
    client, _ = client_env
    cid = client.post("/clientes", json={"nome": "Ana", "telefone": 111, "correntista": True}).json()["id"]
    r = client.get(f"/clientes/{cid}")
    assert r.status_code == 200
    assert r.json()["score_credito"] == 0.0

def test_get_404_detail_preservado(client_env):
    client, _ = client_env
    r = client.get("/clientes/999999")
    assert r.status_code == 404

def test_get_404_bad_json_usa_mensagem_padrao(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(id_): raise http_status_error_bad_json(404, method="GET", url=f"http://fake-db/clientes/{id_}")
    monkeypatch.setattr(fake_db, "get_cliente", boom)
    r = client.get("/clientes/123")
    assert r.status_code == 404
    assert r.json()["detail"] == "Cliente não encontrado"

def test_get_502_bad_json(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(id_): raise http_status_error_bad_json(500, method="GET", url=f"http://fake-db/clientes/{id_}")
    monkeypatch.setattr(fake_db, "get_cliente", boom)
    r = client.get("/clientes/1")
    assert r.status_code == 502
    assert r.json()["detail"] == "Erro no serviço clientes_db"

def test_get_503_request_error(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(id_): raise request_error("net")
    monkeypatch.setattr(fake_db, "get_cliente", boom)
    r = client.get("/clientes/1")
    assert r.status_code == 503
    assert r.json()["detail"] == "clientes_db indisponível"

def test_list_ok(client_env):
    client, _ = client_env
    client.post("/clientes", json={"nome": "L", "telefone": 222, "correntista": True})
    r = client.get("/clientes")
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert items[0]["score_credito"] == 0.0

def test_list_502_bad_json(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(): raise http_status_error_bad_json(500, method="GET", url="http://fake-db/clientes")
    monkeypatch.setattr(fake_db, "list_clientes", boom)
    r = client.get("/clientes")
    assert r.status_code == 502
    assert r.json()["detail"] == "Erro no serviço clientes_db"

def test_list_503_request_error(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(): raise request_error("timeout")
    monkeypatch.setattr(fake_db, "list_clientes", boom)
    r = client.get("/clientes")
    assert r.status_code == 503
    assert r.json()["detail"] == "clientes_db indisponível"

def test_update_ok(client_env):
    client, _ = client_env
    cid = client.post("/clientes", json={"nome": "U", "telefone": 333, "correntista": True, "saldo_cc": 10.0}).json()["id"]
    r = client.put(f"/clientes/{cid}", json={"saldo_cc": 60.0})
    assert r.status_code == 200
    assert r.json()["score_credito"] == 0.0
    assert r.json()["saldo_cc"] == 60.0

def test_update_404(client_env):
    client, _ = client_env
    r = client.put("/clientes/999", json={"saldo_cc": 1.0})
    assert r.status_code == 404

def test_update_400_regra(client_env):
    client, _ = client_env
    cid = client.post("/clientes", json={"nome": "U2", "telefone": 444, "correntista": True, "saldo_cc": 5.0}).json()["id"]
    r = client.put(f"/clientes/{cid}", json={"saldo_cc": -5.0})
    assert r.status_code == 400

def test_update_422_payload_invalido_do_servico(client_env, monkeypatch):
    client, fake_db = client_env
    cid = client.post("/clientes", json={"nome": "P", "telefone": 555, "correntista": True, "saldo_cc": 5.0}).json()["id"]

    async def boom(id_, payload):
        raise http_status_error(422, "Payload inválido", method="PUT", url=f"http://fake-db/clientes/{id_}")

    monkeypatch.setattr(fake_db, "update_cliente", boom)

    r = client.put(f"/clientes/{cid}", json={"nome": "novo-nome"})  # payload válido
    assert r.status_code == 422
    assert r.json()["detail"] == "Payload inválido"

def test_update_502_bad_json(client_env, monkeypatch):
    client, fake_db = client_env
    cid = client.post("/clientes", json={"nome":"K","telefone":777,"correntista":True,"saldo_cc":1.0}).json()["id"]
    async def boom(id_, payload): raise http_status_error_bad_json(500, method="PUT", url=f"http://fake-db/clientes/{id_}")
    monkeypatch.setattr(fake_db, "update_cliente", boom)
    r = client.put(f"/clientes/{cid}", json={"saldo_cc": 2.0})
    assert r.status_code == 502
    assert r.json()["detail"] == "Erro no serviço clientes_db"

def test_update_503_request_error(client_env, monkeypatch):
    client, fake_db = client_env
    cid = client.post("/clientes", json={"nome":"N","telefone":888,"correntista":True,"saldo_cc":1.0}).json()["id"]
    async def boom(id_, payload): raise request_error("timeout")
    monkeypatch.setattr(fake_db, "update_cliente", boom)
    r = client.put(f"/clientes/{cid}", json={"saldo_cc": 2.0})
    assert r.status_code == 503
    assert r.json()["detail"] == "clientes_db indisponível"

def test_update_payload_vazio_exclude_unset(client_env):

    client, _ = client_env
    cid = client.post("/clientes", json={"nome": "NoFields", "telefone": 999, "correntista": False, "saldo_cc": 15.0}).json()["id"]
    r = client.put(f"/clientes/{cid}", json={})
    assert r.status_code == 200
    assert r.json()["score_credito"] == 0.0

def test_delete_ok_e_confere_404(client_env):
    client, _ = client_env
    cid = client.post("/clientes", json={"nome": "D", "telefone": 555, "correntista": True}).json()["id"]
    assert client.delete(f"/clientes/{cid}").status_code == 204
    assert client.get(f"/clientes/{cid}").status_code == 404

def test_delete_404(client_env):
    client, _ = client_env
    r = client.delete("/clientes/999")
    assert r.status_code == 404

def test_delete_502_bad_json(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(id_): raise http_status_error_bad_json(500, method="DELETE", url=f"http://fake-db/clientes/{id_}")
    monkeypatch.setattr(fake_db, "delete_cliente", boom)
    r = client.delete("/clientes/1")
    assert r.status_code == 502
    assert r.json()["detail"] == "Erro no serviço clientes_db"

def test_delete_503_request_error(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(id_): raise request_error("timeout")
    monkeypatch.setattr(fake_db, "delete_cliente", boom)
    r = client.delete("/clientes/1")
    assert r.status_code == 503
    assert r.json()["detail"] == "clientes_db indisponível"

def test_score_ok_sem_persistir_e_rounding(client_env):
    client, _ = client_env

    cid = client.post("/clientes", json={"nome": "S", "telefone": 666, "correntista": True, "saldo_cc": 10.12345}).json()["id"]
    r = client.get(f"/clientes/{cid}/score_credito")
    assert r.status_code == 200
    assert r.json()["score_credito"] == 1.0123
    assert client.get(f"/clientes/{cid}").json()["score_credito"] == 0.0

def test_score_404(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(id_): raise http_status_error(404, "Cliente não encontrado", method="GET", url=f"http://fake-db/clientes/{id_}")
    monkeypatch.setattr(fake_db, "get_cliente", boom)
    r = client.get("/clientes/999999/score_credito")
    assert r.status_code == 404

def test_score_502_bad_json(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(id_): raise http_status_error_bad_json(500, method="GET", url=f"http://fake-db/clientes/{id_}")
    monkeypatch.setattr(fake_db, "get_cliente", boom)
    r = client.get("/clientes/1/score_credito")
    assert r.status_code == 502
    assert r.json()["detail"] == "Erro no serviço clientes_db"

def test_score_503_request_error(client_env, monkeypatch):
    client, fake_db = client_env
    async def boom(id_): raise request_error("timeout")
    monkeypatch.setattr(fake_db, "get_cliente", boom)
    r = client.get("/clientes/1/score_credito")
    assert r.status_code == 503
    assert r.json()["detail"] == "clientes_db indisponível"

class AsyncClientStubOK:
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc, tb): return False
    async def post(self, url, json=None, timeout=10):
        req = httpx.Request("POST", url)
        return httpx.Response(201, content=b'{"ok":1}', request=req)
    async def get(self, url, timeout=10):
        req = httpx.Request("GET", url)
        if url.endswith("/clientes"):
            return httpx.Response(200, content=b'[{"id":1}]', request=req)
        return httpx.Response(200, content=b'{"id":1}', request=req)
    async def put(self, url, json=None, timeout=10):
        req = httpx.Request("PUT", url)
        return httpx.Response(200, content=b'{"id":1}', request=req)
    async def delete(self, url, timeout=10):
        req = httpx.Request("DELETE", url)
        return httpx.Response(204, content=b"", request=req)

class AsyncClientStubERR:
    def __init__(self, status=500): self.status = status
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc, tb): return False
    async def post(self, url, json=None, timeout=10):
        req = httpx.Request("POST", url); return httpx.Response(self.status, content=b"{}", request=req)
    async def get(self, url, timeout=10):
        req = httpx.Request("GET", url); return httpx.Response(self.status, content=b"{}", request=req)
    async def put(self, url, json=None, timeout=10):
        req = httpx.Request("PUT", url); return httpx.Response(self.status, content=b"{}", request=req)
    async def delete(self, url, timeout=10):
        req = httpx.Request("DELETE", url); return httpx.Response(self.status, content=b"{}", request=req)

def test_dbclient_ok_e_rstrip(monkeypatch):

    monkeypatch.setattr(httpx, "AsyncClient", lambda: AsyncClientStubOK())
    db = DbClient(base_url="http://localhost:8001/")
    import asyncio
    assert asyncio.run(db.create_cliente({})) == {"ok": 1}
    assert asyncio.run(db.get_cliente(1)) == {"id": 1}
    assert asyncio.run(db.list_clientes()) == [{"id": 1}]
    assert asyncio.run(db.update_cliente(1, {})) == {"id": 1}
    assert asyncio.run(db.delete_cliente(1)) is None

def test_dbclient_err(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", lambda: AsyncClientStubERR(500))
    db = DbClient(base_url="http://localhost:8001")
    import asyncio
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(db.create_cliente({}))
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(db.get_cliente(1))
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(db.list_clientes())
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(db.update_cliente(1, {}))
    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(db.delete_cliente(1))


import pytest
import httpx

# --------------------------
# Ajuda para construir erros
# --------------------------
def _http_status_error(status: int, detail):
    req = httpx.Request("GET", "http://x")
    resp = httpx.Response(status, json={"detail": detail})
    return httpx.HTTPStatusError("err", request=req, response=resp)


# --------------------------
# Handlers de validação (422) e fluxos OK (já cobertos)
# --------------------------
@pytest.mark.asyncio
async def test_handler_422_personalizado_api(api_async_client):
    client, _ = api_async_client
    invalido = {
        "agencia": "12",               # curto
        "numero_conta": "ABCD",       # não numérico
        "cpf": "123",                 # curto
        "telefone": 1,               # curto
        "email": "x"                  # inválido
    }
    r = await client.post("/contas", json=invalido)
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["status"] == 422
    assert any(e["campo"] == "cpf" for e in detail["errors"])  # mensagem amigável

@pytest.mark.asyncio
async def test_criar_listar_obter_atualizar_api(api_async_client):
    client, fake = api_async_client
    payload = {
        "agencia": "1234",
        "numero_conta": "5678",
        "nome": "Maria",
        "cpf": "12345678901",
        "telefone": 11999999999,
        "email": "m@ex.com",
        "saldo_cc": 0.0,
    }
    r = await client.post("/contas", json=payload)
    assert r.status_code == 201
    r = await client.get("/contas")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    r = await client.get("/contas/1234/5678")
    assert r.status_code == 200
    r = await client.put("/contas/1234/5678", json={"nome": "Maria Atual"})
    assert r.status_code == 200
    assert r.json()["nome"] == "Maria Atual"

@pytest.mark.asyncio
async def test_desativar_fluxo_api(api_async_client):
    client, fake = api_async_client
    # saldo não zero
    async def fake_obter_conta_naozerado(ag, num):
        return {"saldo_cc": 10.0}
    fake.obter_conta = fake_obter_conta_naozerado
    r = await client.delete("/contas/1234/5678/desativar")
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "SALDO_NAO_ZERADO"

    # saldo zero
    async def fake_obter_conta_zerado(ag, num):
        return {"saldo_cc": 0.0}
    fake.obter_conta = fake_obter_conta_zerado
    called = {"ok": False}
    async def fake_desativar(ag, num):
        called["ok"] = True
        return None
    fake.desativar_conta = fake_desativar
    r = await client.delete("/contas/1234/5678/desativar")
    assert r.status_code == 204
    assert called["ok"] is True

@pytest.mark.asyncio
async def test_operacoes_api(api_async_client):
    client, _ = api_async_client
    r = await client.post("/contas/operacoes/depositar", json={"agencia": "1234", "numero_conta": "5678", "saldo": 50.0})
    assert r.status_code == 200
    r = await client.post("/contas/operacoes/sacar", json={"agencia": "1234", "numero_conta": "5678", "saldo": 10.0})
    assert r.status_code == 200

@pytest.mark.asyncio
async def test_cheque_especial_api(api_async_client):
    client, fake = api_async_client
    # obter_conta deve retornar id para o fluxo da rota
    async def obter_com_id(ag, num):
        return {"id": 99}
    fake.obter_conta = obter_com_id
    async def cadastrar(id_, payload):
        return {
            "agencia": payload["agencia"],
            "numero_conta": payload["numero_conta"],
            "cheque_especial_contratado": payload["habilitado"],
            "limite_cheque_especial": payload["limite"],
            "nome": "X",
            "telefone": 11999999999,
            "cpf": "12345678901",
            "email": "x@x.com",
            "correntista": True,
            "saldo_cc": 0.0,
            "limite_atual": payload["limite"],
            "score_credito": 0.0,
        }
    fake.cadastrar_cheque_especial = cadastrar
    r = await client.put("/contas/1234/5678/cheque_especial/cadastrar", json={"habilitado": True, "limite": 100.0})
    assert r.status_code == 200
    body = r.json()
    assert body["cheque_especial_contratado"] is True
    assert body["limite_cheque_especial"] == 100.0

@pytest.mark.asyncio
async def test_score_credito_api(api_async_client):
    client, fake = api_async_client
    async def obter_pos(ag, num):
        return {"saldo_cc": 200.0}
    fake.obter_conta = obter_pos
    r = await client.get("/contas/1234/5678/score_credito")
    assert r.status_code == 200
    assert r.json()["score_credito"] == 20.0

    async def obter_neg(ag, num):
        return {"saldo_cc": -10.0}
    fake.obter_conta = obter_neg
    r = await client.get("/contas/1234/5678/score_credito")
    assert r.status_code == 200
    assert r.json()["score_credito"] == 0.0


# ----------------------------------------------------
# Cobertura dos ramos de erro por endpoint (API)
# ----------------------------------------------------
@pytest.mark.asyncio
async def test_api_requesterror_por_endpoint(api_async_client):
    client, fake = api_async_client

    # 1) POST /contas -> criar_conta (RequestError mapeado p/ 503)
    async def boom_criar(payload=None):
        raise httpx.RequestError("unavailable", request=httpx.Request("POST", "http://x"))
    fake.criar_conta = boom_criar
    r = await client.post("/contas", json={
        "agencia": "1234", "numero_conta": "5678", "nome": "AA",
        "cpf": "12345678901", "telefone": 11999999999, "email": "a@a.com"
    })
    assert r.status_code == 503
    assert r.json()["detail"]["code"] == "CLIENTES_DB_INDISPONIVEL"

    # 2) GET /contas -> listar_contas
    async def boom_listar():
        raise httpx.RequestError("unavailable", request=httpx.Request("GET", "http://x"))
    fake.listar_contas = boom_listar
    r = await client.get("/contas")
    assert r.status_code == 503

    # 3) GET /contas/{ag}/{num} -> obter_conta
    async def boom_obter(ag, num):
        raise httpx.RequestError("unavailable", request=httpx.Request("GET", "http://x"))
    fake.obter_conta = boom_obter
    r = await client.get("/contas/111/2222")
    assert r.status_code == 503

    # 4) PUT /contas/{ag}/{num} -> atualizar_conta
    async def boom_atualizar(ag, num, payload):
        raise httpx.RequestError("unavailable", request=httpx.Request("PUT", "http://x"))
    fake.atualizar_conta = boom_atualizar
    r = await client.put("/contas/111/2222", json={"nome": "BB"})
    assert r.status_code == 503

    # 5) DELETE /contas/{ag}/{num}/desativar -> usar HTTPStatusError (o endpoint trata esse caso)
    async def ok_obter(ag, num):  # permitir chegar à chamada de desativar
        return {"saldo_cc": 0.0}
    fake.obter_conta = ok_obter

    async def err_desativar(ag, num):
        # usar HTTPStatusError porque o endpoint captura esse tipo (não RequestError)
        raise _http_status_error(409, {"status": 409, "code": "CONFLITO_DEL", "message": "..."})
    fake.desativar_conta = err_desativar

    r = await client.delete("/contas/111/2222/desativar")
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "CONFLITO_DEL"

    # 6) POST /contas/operacoes/depositar -> depositar
    async def boom_depositar(payload=None):
        raise httpx.RequestError("unavailable", request=httpx.Request("POST", "http://x"))
    fake.depositar = boom_depositar
    r = await client.post("/contas/operacoes/depositar", json={"agencia": "123", "numero_conta": "0000", "saldo": 1.0})
    assert r.status_code == 503

    # 7) POST /contas/operacoes/sacar -> sacar
    async def boom_sacar(payload=None):
        raise httpx.RequestError("unavailable", request=httpx.Request("POST", "http://x"))
    fake.sacar = boom_sacar
    r = await client.post("/contas/operacoes/sacar", json={"agencia": "123", "numero_conta": "0000", "saldo": 1.0})
    assert r.status_code == 503

    # 8) PUT /contas/{ag}/{num}/cheque_especial/cadastrar -> cadastrar_cheque_especial
    async def ok_obter_id(ag, num):
        return {"id": 7}
    fake.obter_conta = ok_obter_id
    async def boom_cheque(id_, payload=None):
        raise httpx.RequestError("unavailable", request=httpx.Request("PUT", "http://x"))
    fake.cadastrar_cheque_especial = boom_cheque
    r = await client.put("/contas/123/0000/cheque_especial/cadastrar", json={"habilitado": True, "limite": 10.0})
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_api_httpstatuserror_por_endpoint(api_async_client):
    client, fake = api_async_client

    # 1) POST /contas
    async def err_criar(payload=None):
        raise _http_status_error(409, {"status": 409, "code": "CONTA_DUPLICADA", "message": "dup"})
    fake.criar_conta = err_criar
    r = await client.post("/contas", json={
        "agencia": "1234", "numero_conta": "5678", "nome": "BB",
        "cpf": "12345678901", "telefone": 11999999999, "email": "a@a.com"
    })
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "CONTA_DUPLICADA"

    # 2) GET /contas
    async def err_listar():
        raise _http_status_error(500, {"status": 500, "code": "X", "message": "Y"})
    fake.listar_contas = err_listar
    r = await client.get("/contas")
    assert r.status_code == 500
    assert r.json()["detail"]["code"] == "X"

    # 3) GET /contas/{ag}/{num}
    async def err_obter(ag, num):
        raise _http_status_error(404, {"status": 404, "code": "NAO", "message": "sem"})
    fake.obter_conta = err_obter
    r = await client.get("/contas/111/2222")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "NAO"

    # 4) PUT /contas/{ag}/{num}
    async def err_atualizar(ag, num, payload):
        raise _http_status_error(400, {"status": 400, "code": "REQ", "message": "inv"})
    fake.atualizar_conta = err_atualizar
    r = await client.put("/contas/111/2222", json={"nome": "CC"})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "REQ"

    # 5) DELETE /contas/{ag}/{num}/desativar (saldo zerado p/ chamar desativar)
    async def ok_obter(ag, num):
        return {"saldo_cc": 0.0}
    fake.obter_conta = ok_obter
    async def err_desativar(ag, num):
        raise _http_status_error(409, {"status": 409, "code": "CONFLITO", "message": "n pode"})
    fake.desativar_conta = err_desativar
    r = await client.delete("/contas/111/2222/desativar")
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "CONFLITO"

    # 6) POST /contas/operacoes/depositar
    async def err_depositar(payload=None):
        raise _http_status_error(422, {"status": 422, "code": "VAL", "message": "bad"})
    fake.depositar = err_depositar
    r = await client.post("/contas/operacoes/depositar", json={"agencia": "123", "numero_conta": "0000", "saldo": 1.0})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "VAL"

    # 7) POST /contas/operacoes/sacar
    async def err_sacar(payload=None):
        raise _http_status_error(409, {"status": 409, "code": "SALDO_INSUFICIENTE", "message": "..."})
    fake.sacar = err_sacar
    r = await client.post("/contas/operacoes/sacar", json={"agencia": "123", "numero_conta": "0000", "saldo": 1.0})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "SALDO_INSUFICIENTE"

    # 8) PUT /contas/{ag}/{num}/cheque_especial/cadastrar
    async def ok_obter_id(ag, num):
        return {"id": 7}
    fake.obter_conta = ok_obter_id
    async def err_cheque(id_, payload=None):
        raise _http_status_error(400, {"status": 400, "code": "CHEQUE_ERR", "message": "..."})
    fake.cadastrar_cheque_especial = err_cheque
    r = await client.put("/contas/123/0000/cheque_especial/cadastrar", json={"habilitado": True, "limite": 10.0})
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "CHEQUE_ERR"


# ----------------------------------
# Extra: erro no score (HTTPStatus)
# ----------------------------------
@pytest.mark.asyncio
async def test_score_credito_httpstatuserror(api_async_client):
    client, fake = api_async_client
    async def boom(ag, num):
        raise _http_status_error(404, {"status": 404, "code": "NAO", "message": "sem"})
    fake.obter_conta = boom
    r = await client.get("/contas/111/2222/score_credito")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "NAO"

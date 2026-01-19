
def test_criar_e_listar_contas(db_test_client):
    c = db_test_client
    payload = {
        "agencia": "1234",
        "numero_conta": "567890",
        "nome": "Maria Silva",
        "cpf": "12345678901",
        "telefone": 11999999999,
        "email": "maria@ex.com",
        "correntista": True,
        "saldo_cc": 100.0,
        "cheque_especial_contratado": False,
        "limite_cheque_especial": 0.0,
    }
    r = c.post("/contas", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["agencia"] == "1234"
    assert body["saldo_cc"] == 100.0
    assert body["limite_atual"] == 0.0
    assert body["score_credito"] == 10.0

    # Listar
    r = c.get("/contas")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) == 1

    # Buscar por chaves
    r = c.get("/contas/1234/567890")
    assert r.status_code == 200
    assert r.json()["cpf"] == "12345678901"

def test_validacoes_criacao(db_test_client):
    c = db_test_client
    # Saldo inicial negativo -> precisa que o resto esteja válido para cair na regra de negócio
    payload = {
        "agencia": "1234",
        "numero_conta": "0001",
        "nome": "Ana",  # min_length=2
        "cpf": "12345678902",
        "telefone": 11999999999,
        "email": "a@a.com",
        "correntista": True,
        "saldo_cc": -1.0,
    }
    r = c.post("/contas", json=payload)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "SALDO_NEGATIVO_INICIAL"

    # correntista=False exige saldo 0
    payload.update({"saldo_cc": 10.0, "correntista": False})
    r = c.post("/contas", json=payload)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "SALDO_INVALIDO_CORRENTISTA_FALSE"

    # cheque especial habilitado com limite inválido (usar None para passar no schema e cair na regra da rota)
    payload.update({
        "saldo_cc": 0.0,
        "correntista": True,
        "cheque_especial_contratado": True,
        "limite_cheque_especial": None,  # aciona a regra da rota
        "cpf": "12345678903"
    })
    r = c.post("/contas", json=payload)
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "LIMITE_CHEQUE_ESPECIAL_INVALIDO"

def test_conflitos_unicidade(db_test_client):
    c = db_test_client
    base = {
        "agencia": "123",
        "numero_conta": "1111",
        "nome": "Joao",
        "cpf": "99999999999",
        "telefone": 11999999999,
        "email": "j@j.com",
    }
    r = c.post("/contas", json=base | {"saldo_cc": 0.0})
    assert r.status_code == 201

    # Duplicidade agencia+numero
    r = c.post("/contas", json=base | {"cpf": "88888888888", "saldo_cc": 0.0})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] in ("CONTA_DUPLICADA", "CONFLITO_UNICO")

    # Duplicidade CPF
    r = c.post("/contas", json={**base, "numero_conta": "2222", "saldo_cc": 0.0})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "CPF_JA_CADASTRADO"

def test_atualizar_e_regras(db_test_client):
    c = db_test_client
    payload = {
        "agencia": "1234",
        "numero_conta": "5678",
        "nome": "Maria",
        "cpf": "12312312312",
        "telefone": 11999999999,
        "email": "m@ex.com",
        "saldo_cc": 50.0,
    }
    assert c.post("/contas", json=payload).status_code == 201

    # Bloqueio correntista=False com saldo != 0
    r = c.put("/contas/1234/5678", json={"correntista": False})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "SALDO_INVALIDO_CORRENTISTA_FALSE"

    # Atualização parcial OK
    r = c.put("/contas/1234/5678", json={"nome": "Maria Atual"})
    assert r.status_code == 200
    assert r.json()["nome"] == "Maria Atual"

def test_operacoes_deposito_saque_e_cheque(db_test_client):
    c = db_test_client
    payload = {
        "agencia": "0101",
        "numero_conta": "9999",
        "nome": "Ca",  # min_length=2
        "cpf": "01010101010",
        "telefone": 11999999999,
        "email": "c@ex.com",
        "saldo_cc": 0.0,
    }
    assert c.post("/contas", json=payload).status_code == 201

    # Depositar
    r = c.post("/contas/operacoes/depositar", json={"agencia": "0101", "numero_conta": "9999", "saldo": 120.0})
    assert r.status_code == 200
    assert r.json()["saldo_cc"] == 120.0

    # Sacar com saldo suficiente
    r = c.post("/contas/operacoes/sacar", json={"agencia": "0101", "numero_conta": "9999", "saldo": 20.0})
    assert r.status_code == 200
    assert r.json()["saldo_cc"] == 100.0

    # Sacar sem cheque especial e sem saldo
    r = c.post("/contas/operacoes/sacar", json={"agencia": "0101", "numero_conta": "9999", "saldo": 200.0})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "SALDO_INSUFICIENTE"

    # Habilitar cheque especial (por ID): buscar a conta para pegar ID
    r = c.get("/contas/0101/9999")
    conta_id = r.json()["id"]
    r2 = c.put(f"/contas/{conta_id}/cheque_especial/cadastrar", json={"habilitado": True, "limite": 100.0})
    assert r2.status_code == 200
    assert r2.json()["cheque_especial_contratado"] is True

    # Sacar usando limite dentro do permitido
    r = c.post("/contas/operacoes/sacar", json={"agencia": "0101", "numero_conta": "9999", "saldo": 150.0})
    assert r.status_code == 200
    assert r.json()["saldo_cc"] == -50.0

    # Tentar exceder limite
    r = c.post("/contas/operacoes/sacar", json={"agencia": "0101", "numero_conta": "9999", "saldo": 60.0})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "CHEQUE_ESPECIAL_EXCEDIDO"

    # Não pode desabilitar com saldo negativo
    r = c.put(f"/contas/{conta_id}/cheque_especial/cadastrar", json={"habilitado": False, "limite": 0.0})
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "CHEQUE_ESPECIAL_COM_SALDO_NEGATIVO"

def test_desativar_fluxo(db_test_client):
    c = db_test_client
    payload = {
        "agencia": "7777",
        "numero_conta": "0001",
        "nome": "Ze",  # min_length=2 (ajuste final)
        "cpf": "77777777777",
        "telefone": 11999999999,
        "email": "z@z.com",
        "saldo_cc": 10.0,
    }
    assert c.post("/contas", json=payload).status_code == 201

    # Não permite desativar com saldo != 0
    r = c.delete("/contas/7777/0001/desativar")
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "SALDO_NAO_ZERADO"

    # Zerar saldo
    c.post("/contas/operacoes/sacar", json={"agencia": "7777", "numero_conta": "0001", "saldo": 10.0})
    r = c.delete("/contas/7777/0001/desativar")
    assert r.status_code == 204

    # Verificar que não existe mais
    r = c.get("/contas/7777/0001")
    assert r.status_code == 404

def test_handler_422_personalizado_db(db_test_client):
    c = db_test_client
    invalido = {
        "agencia": "12",               # muito curto
        "numero_conta": "abc",         # não numérico
        "nome": "A",
        "cpf": "123",                  # muito curto
        "telefone": 1,                 # muito curto
        "email": "x",                  # inválido
    }
    r = c.post("/contas", json=invalido)
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert detail["status"] == 422
    assert detail["code"] == "VALIDACAO_REQUISICAO"
    assert any(e["campo"] == "agencia" for e in detail["errors"])

def test_nao_encontrada_404(db_test_client):
    c = db_test_client
    r = c.get("/contas/000/9999")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "CONTA_NAO_ENCONTRADA"

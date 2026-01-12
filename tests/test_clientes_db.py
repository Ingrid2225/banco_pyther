
import os, sys
import pytest
from fastapi.testclient import TestClient


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


from clientes_db.app.main import app
from clientes_db.app.db import Base, engine, get_db


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_main_app_import():

    assert hasattr(app, "openapi")

def test_get_db_generator_closes():
    gen = get_db()
    db = next(gen)
    assert db is not None
    with pytest.raises(StopIteration):
        next(gen)

@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c

def test_create_cliente_201(client):
    r = client.post("/clientes", json={
        "nome": "Maria Silva",
        "telefone": 11999999999,
        "correntista": True,
        "saldo_cc": 100.0
    })
    assert r.status_code == 201
    body = r.json()
    assert body["id"] > 0
    assert body["saldo_cc"] == 100.0

def test_create_cliente_saldo_negativo_422(client):
    r = client.post("/clientes", json={
        "nome": "Joao Souza",
        "telefone": 11988888888,
        "correntista": False,
        "saldo_cc": -1.0
    })
    assert r.status_code == 422

def test_get_cliente_200_e_404(client):

    cid = client.post("/clientes", json={
        "nome": "Ana Paula",
        "telefone": 111,
        "correntista": True,
        "saldo_cc": 50.0
    }).json()["id"]

    r_ok = client.get(f"/clientes/{cid}")
    assert r_ok.status_code == 200
    assert r_ok.json()["id"] == cid

    r_404 = client.get("/clientes/999999")
    assert r_404.status_code == 404

def test_list_clientes_200(client):
    client.post("/clientes", json={
        "nome": "Luis Carlos",
        "telefone": 222,
        "correntista": True,
        "saldo_cc": 0.0
    })
    r = client.get("/clientes")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1

def test_update_cliente_200_400_404(client):

    cid = client.post("/clientes", json={
        "nome": "Usuario Um",
        "telefone": 333,
        "correntista": False,
        "saldo_cc": 10.0
    }).json()["id"]

    r_ok = client.put(f"/clientes/{cid}", json={"saldo_cc": 60.0})
    assert r_ok.status_code == 200
    assert r_ok.json()["saldo_cc"] == 60.0

    r_bad = client.put(f"/clientes/{cid}", json={"saldo_cc": -5.0})
    assert r_bad.status_code == 400

    r_404 = client.put("/clientes/999999", json={"saldo_cc": 1.0})
    assert r_404.status_code == 404

def test_delete_cliente_204_e_404(client):

    cid = client.post("/clientes", json={
        "nome": "Diego Ramos",
        "telefone": 444,
        "correntista": True,
        "saldo_cc": 0.0
    }).json()["id"]

    r_del = client.delete(f"/clientes/{cid}")
    assert r_del.status_code == 204

    r_get = client.get(f"/clientes/{cid}")
    assert r_get.status_code == 404

def test_update_cliente_atualiza_todos_os_campos_true_branches(client):

    cid = client.post("/clientes", json={
        "nome": "Original Nome",
        "telefone": 5550001,
        "correntista": False,
        "saldo_cc": 1.0
    }).json()["id"]

    r = client.put(f"/clientes/{cid}", json={
        "nome": "Novo Nome",
        "telefone": 5550002,
        "correntista": True,
        "saldo_cc": 2.5
    })
    assert r.status_code == 200
    body = r.json()
    assert body["nome"] == "Novo Nome"
    assert body["telefone"] == 5550002
    assert body["correntista"] is True
    assert body["saldo_cc"] == 2.5

def test_update_cliente_body_vazio_false_branches(client):

    cid = client.post("/clientes", json={
        "nome": "SemUpdate Nome",
        "telefone": 7771000,
        "correntista": True,
        "saldo_cc": 15.0
    }).json()["id"]


    r = client.put(f"/clientes/{cid}", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["nome"] == "SemUpdate Nome"
    assert body["telefone"] == 7771000
    assert body["correntista"] is True
    assert body["saldo_cc"] == 15.0

def test_list_clientes_vazio_caminho_sem_itens(client):

    r = client.get("/clientes")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_delete_cliente_return_none_endpoint(client):

    cid = client.post("/clientes", json={
        "nome": "Para Deletar",
        "telefone": 9991000,
        "correntista": False,
        "saldo_cc": 0.0
    }).json()["id"]

    r = client.delete(f"/clientes/{cid}")
    assert r.status_code == 204
    assert client.get(f"/clientes/{cid}").status_code == 404

def test_update_cliente_apenas_telefone_branch_isolado(client):

    cid = client.post("/clientes", json={
        "nome": "Branch Telefone",
        "telefone": 990001,
        "correntista": False,
        "saldo_cc": 12.0
    }).json()["id"]

    r = client.put(f"/clientes/{cid}", json={"telefone": 990002})
    assert r.status_code == 200
    body = r.json()
    assert body["telefone"] == 990002
    assert body["nome"] == "Branch Telefone"
    assert body["correntista"] is False
    assert body["saldo_cc"] == 12.0

def test_update_cliente_apenas_nome_branch_isolado(client):

    cid = client.post("/clientes", json={
        "nome": "Nome Antigo",
        "telefone": 880001,
        "correntista": False,
        "saldo_cc": 7.0
    }).json()["id"]

    r = client.put(f"/clientes/{cid}", json={"nome": "Nome Novo"})
    assert r.status_code == 200
    body = r.json()
    assert body["nome"] == "Nome Novo"
    assert body["telefone"] == 880001
    assert body["correntista"] is False
    assert body["saldo_cc"] == 7.0

def test_update_cliente_apenas_correntista_branch_isolado(client):

    cid = client.post("/clientes", json={
        "nome": "Flag Corr",
        "telefone": 770001,
        "correntista": False,
        "saldo_cc": 8.5
    }).json()["id"]

    r = client.put(f"/clientes/{cid}", json={"correntista": True})
    assert r.status_code == 200
    body = r.json()
    assert body["correntista"] is True
    assert body["nome"] == "Flag Corr"
    assert body["telefone"] == 770001
    assert body["saldo_cc"] == 8.5

def test_update_cliente_apenas_saldo_zero_branch_isolado(client):

    cid = client.post("/clientes", json={
        "nome": "Saldo Zero",
        "telefone": 660001,
        "correntista": True,
        "saldo_cc": 9.9
    }).json()["id"]

    r = client.put(f"/clientes/{cid}", json={"saldo_cc": 0.0})
    assert r.status_code == 200
    body = r.json()
    assert body["saldo_cc"] == 0.0
    assert body["nome"] == "Saldo Zero"
    assert body["telefone"] == 660001
    assert body["correntista"] is True

def test_create_cliente_sem_saldo_opcional_branch(client):

    r = client.post("/clientes", json={
        "nome": "Sem Saldo",
        "telefone": 123456789,
        "correntista": True
    })
    assert r.status_code == 201
    body = r.json()
    assert "id" in body
    assert isinstance(body["saldo_cc"], (int, float))


def test_404_branches_isolados_router(client):

    inexistente = 1

    r_get = client.get(f"/clientes/{inexistente}")
    assert r_get.status_code == 404

    r_put = client.put(f"/clientes/{inexistente}", json={"nome": "Nao Existe"})
    assert r_put.status_code == 404

    r_del = client.delete(f"/clientes/{inexistente}")
    assert r_del.status_code == 404


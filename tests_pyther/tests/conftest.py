
import pytest
import pytest_asyncio
import httpx
from fastapi.testclient import TestClient
from httpx import ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# ---- clientes_db (sync app) fixtures ----
@pytest.fixture(scope="function")
def db_test_client():
    from clientes_db.app.main import app as db_app
    from clientes_db.app.db import Base, get_db

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    db_app.dependency_overrides[get_db] = override_get_db
    client = TestClient(db_app)
    try:
        yield client
    finally:
        db_app.dependency_overrides.clear()

# ---- clientes_api (async app) fixture ----
@pytest_asyncio.fixture(scope="function")
async def api_async_client():
    """
    Retorna (httpx.AsyncClient, fake_db) para o gateway.
    Usa ASGITransport (httpx>=0.28) e evita o erro de async fixture.
    """
    from clientes_api.app.main import app as api_app
    from clientes_api.app.routers.contas import get_db as api_get_db

    class FakeDb:
        async def criar_conta(self, payload):
            return {
                "agencia": payload["agencia"],
                "numero_conta": payload["numero_conta"],
                "nome": payload.get("nome", "Nome"),
                "telefone": payload.get("telefone", 11999999999),
                "cpf": payload.get("cpf", "12345678901"),
                "email": payload.get("email", "a@b.com"),
                "correntista": payload.get("correntista", True),
                "saldo_cc": float(payload.get("saldo_cc", 0.0)),
                "cheque_especial_contratado": payload.get("cheque_especial_contratado", False),
                "limite_cheque_especial": float(payload.get("limite_cheque_especial", 0.0)),
                "limite_atual": float(payload.get("limite_cheque_especial", 0.0)),
                "score_credito": 0.0,
            }

        async def listar_contas(self):
            return [{
                "agencia": "1234",
                "numero_conta": "5678",
                "nome": "Maria",
                "telefone": 11999999999,
                "cpf": "12345678901",
                "email": "maria@ex.com",
                "correntista": True,
                "saldo_cc": 100.0,
                "cheque_especial_contratado": False,
                "limite_cheque_especial": 0.0,
                "limite_atual": 0.0,
                "score_credito": 10.0,
            }]

        async def obter_conta(self, agencia, numero_conta):
            return {
                "id": 1,
                "agencia": agencia,
                "numero_conta": numero_conta,
                "nome": "Maria",
                "telefone": 11999999999,
                "cpf": "12345678901",
                "email": "maria@ex.com",
                "correntista": True,
                "saldo_cc": 100.0,
                "cheque_especial_contratado": False,
                "limite_cheque_especial": 0.0,
                "limite_atual": 0.0,
                "score_credito": 10.0,
            }

        async def atualizar_conta(self, agencia, numero_conta, payload):
            base = await self.obter_conta(agencia, numero_conta)
            base.update(payload)
            return base

        async def desativar_conta(self, agencia, numero_conta):
            return None

        async def depositar(self, payload):
            return await self.obter_conta(payload["agencia"], payload["numero_conta"])

        async def sacar(self, payload):
            return await self.obter_conta(payload["agencia"], payload["numero_conta"])

        async def cadastrar_cheque_especial(self, id_, payload):
            base = await self.obter_conta(payload["agencia"], payload["numero_conta"])
            base.update({
                "cheque_especial_contratado": payload.get("habilitado", False),
                "limite_cheque_especial": payload.get("limite", 0.0)
            })
            return base

    fake = FakeDb()

    def override_get_db():
        return fake

    api_app.dependency_overrides[api_get_db] = override_get_db
    transport = ASGITransport(app=api_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, fake
    api_app.dependency_overrides.clear()

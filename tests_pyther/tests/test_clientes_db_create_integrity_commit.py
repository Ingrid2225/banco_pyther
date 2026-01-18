
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from clientes_db.app.db import Base
from clientes_db.app.schemas import ContaCreate
from clientes_db.app.routers.contas import criar_conta

def _session_mem():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()

def test_criar_conta_integrityerror_no_commit(monkeypatch):
    db = _session_mem()

    body = ContaCreate(
        agencia="1234", numero_conta="0001",
        nome="Ana", cpf="12345678901", telefone=11999999999, email="a@a.com",
        saldo_cc=0.0, correntista=True, cheque_especial_contratado=False, limite_cheque_especial=0.0
    )

    def bad_commit():
        raise IntegrityError("stmt", {}, Exception("dup"))

    monkeypatch.setattr(db, "commit", bad_commit)

    with pytest.raises(HTTPException) as exc:
        criar_conta(body=body, db=db)
    assert exc.value.status_code == 409
    assert exc.value.detail["code"] == "CONFLITO_UNICO"


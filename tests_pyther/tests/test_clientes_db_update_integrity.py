
import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import IntegrityError

from clientes_db.app.db import Base
from clientes_db.app.models import Conta
from clientes_db.app.schemas import ContaCreate, ChequeEspecialCadastro
from clientes_db.app.routers.contas import criar_conta, cadastrar_cheque_especial

def _session_mem():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()

def test_criar_conta_integrityerror_simulado_monkeypatch(monkeypatch):
    #Fiz esse teste pra cobrir a linha 91-95 mas mesmo assim não deu certo
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

def test_cadastrar_cheque_especial_sucesso_cobre_retorno_final():
    #Para cobrir a linha 267 também
    db = _session_mem()
    c = Conta(
        agencia="2222", numero_conta="9999", nome="Carla",
        cpf="33333333333", telefone=11999999999, email="c@ex.com",
        correntista=True, saldo_cc=0.0, cheque_especial_contratado=False, limite_cheque_especial=0.0
    )
    db.add(c); db.commit(); db.refresh(c)

    body = ChequeEspecialCadastro(habilitado=True, limite=0.0)
    out = cadastrar_cheque_especial(id=c.id, body=body, db=db)
    assert out["cheque_especial_contratado"] is True
    assert out["limite_cheque_especial"] == 0.0

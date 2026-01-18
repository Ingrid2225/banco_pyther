
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from clientes_db.app.db import Base
from clientes_db.app.models import Conta
from clientes_db.app.schemas import ChequeEspecialCadastro
from clientes_db.app.routers.contas import cadastrar_cheque_especial

def _session_mem():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()

def test_cheque_especial_retorno_final():
    db = _session_mem()
    conta = Conta(
        agencia="8888", numero_conta="1234", nome="Carla",
        cpf="99999999999", telefone=11999999999, email="c@ex.com",
        correntista=True, saldo_cc=0.0,
        cheque_especial_contratado=False, limite_cheque_especial=0.0
    )
    db.add(conta); db.commit(); db.refresh(conta)

    body = ChequeEspecialCadastro(habilitado=True, limite=0.0)
    saida = cadastrar_cheque_especial(id=conta.id, body=body, db=db)
    assert saida["cheque_especial_contratado"] is True
    assert saida["limite_cheque_especial"] == 0.0

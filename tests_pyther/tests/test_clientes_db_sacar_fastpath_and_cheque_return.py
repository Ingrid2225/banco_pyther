
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from clientes_db.app.db import Base
from clientes_db.app.models import Conta
from clientes_db.app.schemas import OperacaoPorChaves, ChequeEspecialCadastro
from clientes_db.app.routers.contas import sacar, cadastrar_cheque_especial

def _session_mem():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)()

def test_sacar_fastpath_novo_saldo_maior_igual_zero():
    """Cobre ramo rápido do sacar (novo_saldo >= 0) e o return (~176–178)."""
    db = _session_mem()
    conta = Conta(
        agencia="5555", numero_conta="1212", nome="Rick",
        cpf="55555555555", telefone=11999999999, email="r@ex.com",
        correntista=True, saldo_cc=200.0,
        cheque_especial_contratado=False, limite_cheque_especial=0.0
    )
    db.add(conta); db.commit(); db.refresh(conta)

    # IMPORTANTE: schema do clientes_db usa alias "saldo"
    body = OperacaoPorChaves(agencia="5555", numero_conta="1212", saldo=50.0)
    out = sacar(body=body, db=db)
    assert out["saldo_cc"] == 150.0  # 200 - 50

def test_cheque_especial_return_final():
    """Cobre o return final do endpoint de cheque especial (~linha 267)."""
    db = _session_mem()
    conta = Conta(
        agencia="4444", numero_conta="3434", nome="Morty",
        cpf="44444444444", telefone=11999999999, email="m@ex.com",
        correntista=True, saldo_cc=0.0,
        cheque_especial_contratado=False, limite_cheque_especial=0.0
    )
    db.add(conta); db.commit(); db.refresh(conta)

    body = ChequeEspecialCadastro(habilitado=True, limite=0.0)
    out = cadastrar_cheque_especial(id=conta.id, body=body, db=db)
    assert out["cheque_especial_contratado"] is True
    assert out["limite_cheque_especial"] == 0.0


from fastapi import HTTPException
from clientes_db.app.models import Conta
from clientes_db.app.routers.contas import _to_out, _get_by_id_or_404
from clientes_db.app.db import get_db


def test_to_out_branches_limite_atual_e_score():
    # Branch 1: cheque especial contratado e saldo negativo -> limite_atual = max(0, limite + saldo)
    c1 = Conta(
        agencia="0001",
        numero_conta="1234",
        nome="Ana",
        cpf="00000000000",
        telefone=11999999999,
        email="a@a.com",
        correntista=True,
        saldo_cc=-20.0,
        cheque_especial_contratado=True,
        limite_cheque_especial=100.0,
    )
    c1.id = 1
    out1 = _to_out(c1)
    assert out1["limite_atual"] == 80.0  # 100 - 20
    assert out1["score_credito"] == 0.0  # saldo < 0

    # Branch 2: sem cheque especial (ou saldo >= 0) -> limite_atual = limite
    c2 = Conta(
        agencia="0001",
        numero_conta="9999",
        nome="Bia",
        cpf="11111111111",
        telefone=11999999999,
        email="b@b.com",
        correntista=True,
        saldo_cc=50.0,
        cheque_especial_contratado=False,
        limite_cheque_especial=500.0,
    )
    c2.id = 2
    out2 = _to_out(c2)
    assert out2["limite_atual"] == 500.0
    assert out2["score_credito"] == 5.0  # 10% de 50


def test_get_by_id_or_404_lanca_404_para_id_inexistente():
    # Usa o get_db real só para obter uma Session "viva" rapidamente
    gen = get_db()
    db = next(gen)
    try:
        try:
            _get_by_id_or_404(db, id_=999999)
            assert False, "Deveria ter lançado HTTPException 404"
        except HTTPException as exc:
            assert exc.status_code == 404
            assert exc.detail["code"] == "CONTA_NAO_ENCONTRADA"
    finally:
        # fecha a Session do generator
        try:
            next(gen)
        except StopIteration:
            pass


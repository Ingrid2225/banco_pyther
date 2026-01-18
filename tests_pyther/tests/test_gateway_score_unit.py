
import pytest
from clientes_api.app.routers.contas import calcular_score_gateway

class _FakeDb:
    def __init__(self, saldo):
        self._saldo = saldo
    async def obter_conta(self, ag, num):
        return {"saldo_cc": self._saldo}

@pytest.mark.asyncio
async def test_score_credito_unit_saldo_zero():
    db = _FakeDb(0.0)  # aciona explicitamente o return final do endpoint
    resp = await calcular_score_gateway("7", "77", db=db)
    assert resp == {"agencia": "7", "numero_conta": "77", "score_credito": 0.0}

@pytest.mark.asyncio
async def test_score_credito_unit_rounding():
    db = _FakeDb(123.45678)  # aciona round(..., 4)
    resp = await calcular_score_gateway("9", "99", db=db)
    assert resp == {"agencia": "9", "numero_conta": "99", "score_credito": 12.3457}

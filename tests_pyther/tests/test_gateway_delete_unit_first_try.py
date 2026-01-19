
import pytest
import httpx
from fastapi import HTTPException

from clientes_api.app.routers.contas import desativar_conta as desativar_endpoint

class _DbBoomNoObter:
    async def obter_conta(self, agencia, numero_conta):

        raise httpx.RequestError("unavailable", request=httpx.Request("GET", "http://x"))

    async def desativar_conta(self, agencia, numero_conta):
        return None

@pytest.mark.asyncio
async def test_desativar_conta_primeiro_try_requesterror_unit():

    with pytest.raises(HTTPException) as exc:
        await desativar_endpoint("321", "6543", db=_DbBoomNoObter())

    err = exc.value
    assert err.status_code == 503
    assert err.detail["code"] == "CLIENTES_DB_INDISPONIVEL"

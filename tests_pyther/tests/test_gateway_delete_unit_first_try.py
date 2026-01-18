
import pytest
import httpx
from fastapi import HTTPException

# Importa a função do endpoint diretamente
from clientes_api.app.routers.contas import desativar_conta as desativar_endpoint

class _DbBoomNoObter:
    async def obter_conta(self, agencia, numero_conta):
        # Simula falha de rede no PRIMEIRO try do endpoint
        raise httpx.RequestError("unavailable", request=httpx.Request("GET", "http://x"))

    # Os demais não são chamados nesse cenário, mas deixo aqui para não quebrar
    async def desativar_conta(self, agencia, numero_conta):
        return None

@pytest.mark.asyncio
async def test_desativar_conta_primeiro_try_requesterror_unit():
    # Chama a CORROTINA do endpoint diretamente, injetando db que explode em obter_conta
    with pytest.raises(HTTPException) as exc:
        await desativar_endpoint("321", "6543", db=_DbBoomNoObter())

    err = exc.value
    assert err.status_code == 503
    assert err.detail["code"] == "CLIENTES_DB_INDISPONIVEL"

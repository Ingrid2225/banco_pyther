
import pytest
import httpx

@pytest.mark.asyncio
async def test_delete_desativar_requesterror_primeiro_try(api_async_client):
    client, fake = api_async_client

    # 1º try: obter_conta -> RequestError (mapa 503 no except de cima)
    async def boom_obter(ag, num):
        raise httpx.RequestError("unavailable", request=httpx.Request("GET", "http://x"))
    fake.obter_conta = boom_obter

    r = await client.delete("/contas/321/6543/desativar")
    assert r.status_code == 503
    body = r.json()
    assert body["detail"]["code"] == "CLIENTES_DB_INDISPONIVEL"

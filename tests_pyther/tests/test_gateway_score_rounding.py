
import pytest

@pytest.mark.asyncio
async def test_score_credito_rounding_gateway(api_async_client):
    client, fake = api_async_client

    
    async def obter_custom(ag, num):
        return {"saldo_cc": 123.45678}
    fake.obter_conta = obter_custom

    r = await client.get("/contas/777/8888/score_credito")
    assert r.status_code == 200
    body = r.json()
    
    assert body["score_credito"] == 12.3457
    assert body["agencia"] == "777"
    assert body["numero_conta"] == "8888"


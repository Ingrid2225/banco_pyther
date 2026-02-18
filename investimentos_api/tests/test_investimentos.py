import pytest
import pandas as pd


from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime

from investimentos_api.app.main import app
from investimentos_api.app.services.data_client import DataClient
from investimentos_api.app.services import market
from investimentos_api.app.services import rentabilidade_service
from investimentos_api.app.services import renda_fixa_service
client = TestClient(app)


# =====================================================
# DATA CLIENT
# =====================================================

@pytest.mark.asyncio
async def test_create_investimento_payload_invalido():
    dc = DataClient()
    with pytest.raises(Exception):
        await dc.create_investimento({"foo": "bar"})


# =====================================================
# ROUTER - ANALISE TICKER
# =====================================================

def test_analise_ticker_sucesso():
    with patch("investimentos_api.app.routers.investimentos.analise_mercado_unificado",
               return_value={"ticker": "AAA"}):
        resp = client.get("/investimentos/analise/AAA")
        assert resp.status_code == 200


def test_analise_ticker_sem_historico():
    with patch("investimentos_api.app.routers.investimentos.analise_mercado_unificado",
               return_value=None):
        resp = client.get("/investimentos/analise/AAA")
        assert resp.status_code == 200


# =====================================================
# ROUTER - APLICAR / APORTE
# =====================================================

def test_aplicar_fluxo():
    dc = DataClient()
    dc.get_conta = AsyncMock(return_value={"agencia": "1"})
    dc.create_investimento = AsyncMock(return_value={
        "id": str(uuid4()),
        "agencia": "1",
        "numero_conta": "1",
        "tipo_investimento": "ACOES",
        "valor_investido": 100,
        "rentabilidade": 0,
        "ativo": True,
        "ticker": "AAA",
        "data_aplicacao": datetime.utcnow()
    })

    with patch("investimentos_api.app.routers.investimentos.get_dc", return_value=dc):
        resp = client.post("/investimentos/1/1", json={
            "tipo_investimento": "ACOES",
            "valor_investido": 100,
            "ticker": "AAA",
            "data_aplicacao": datetime.utcnow().isoformat()
        })
        assert resp.status_code == 200


def test_aporte_fluxo():
    dc = DataClient()
    dc.get_conta = AsyncMock(return_value={"agencia": "1"})
    dc.create_investimento = AsyncMock(return_value={
        "id": str(uuid4()),
        "agencia": "1",
        "numero_conta": "1",
        "tipo_investimento": "ACOES",
        "valor_investido": 100,
        "rentabilidade": 0,
        "ativo": True,
        "ticker": "AAA",
        "data_aplicacao": datetime.utcnow()
    })

    with patch("investimentos_api.app.routers.investimentos.get_dc", return_value=dc):
        resp = client.post("/investimentos/1/1/aporte", json={
            "tipo_investimento": "ACOES",
            "valor_investido": 100,
            "ticker": "AAA",
            "data_aplicacao": datetime.utcnow().isoformat()
        })
        assert resp.status_code == 201


# =====================================================
# ROUTER - RESGATES
# =====================================================

def test_resgate_parcial():
    dc = DataClient()
    dc.get_conta = AsyncMock(return_value={"agencia": "1"})
    dc.list_investimentos_por_conta = AsyncMock(return_value=[
        {"id": "1", "ticker": "AAA", "valor_investido": 100, "ativo": True}
    ])
    dc.update_investimento = AsyncMock(return_value={"id": "1"})

    with patch("investimentos_api.app.routers.investimentos.get_dc", return_value=dc):
        resp = client.post("/investimentos/1/1/resgatar", json={
            "ticker": "AAA",
            "valor_resgate": 50
        })
        assert resp.status_code == 200


def test_resgate_maior_que_saldo():
    dc = DataClient()
    dc.get_conta = AsyncMock(return_value={"agencia": "1"})
    dc.list_investimentos_por_conta = AsyncMock(return_value=[
        {"id": "1", "ticker": "AAA", "valor_investido": 100, "ativo": True}
    ])

    with patch("investimentos_api.app.routers.investimentos.get_dc", return_value=dc):
        resp = client.post("/investimentos/1/1/resgatar", json={
            "ticker": "AAA",
            "valor_resgate": 200
        })
        assert resp.status_code == 422


def test_resgate_total():
    dc = DataClient()
    dc.get_conta = AsyncMock(return_value={"agencia": "1"})
    dc.list_investimentos_por_conta = AsyncMock(return_value=[
        {"id": "1", "ticker": "AAA", "valor_investido": 100, "ativo": True}
    ])
    dc.resgate_total = AsyncMock(return_value={"id": "1"})

    with patch("investimentos_api.app.routers.investimentos.get_dc", return_value=dc):
        resp = client.post("/investimentos/1/1/resgatar_total", json={
            "ticker": "AAA"
        })
        assert resp.status_code == 200


# =====================================================
# MARKET
# =====================================================

def test_market_download_variacoes():
    df = pd.DataFrame({"Close": [10, 20, 30]})

    with patch("investimentos_api.app.services.market.yf.download", return_value=df):
        assert len(market._download_close("AAA")) == 3

    df2 = pd.DataFrame({"Open": [1, 2, 3]})
    with patch("investimentos_api.app.services.market.yf.download", return_value=df2):
        with pytest.raises(ValueError):
            market._download_close("AAA")


def test_analise_mercado():
    close = pd.Series([10, 20, 30])
    with patch("investimentos_api.app.services.market._download_close", return_value=close):
        result = market.analise_mercado("AAA")
        assert "retorno_acumulado" in result


def test_analise_unificado():
    hist = pd.DataFrame({"Close": [10, 20, 30]})
    mock_ticker = MagicMock()
    mock_ticker.history.return_value = hist

    with patch("investimentos_api.app.services.market.yf.Ticker", return_value=mock_ticker):
        result = market.analise_mercado_unificado("AAA")
        assert result["ticker"]

    mock_ticker.history.return_value = pd.DataFrame()
    with patch("investimentos_api.app.services.market.yf.Ticker", return_value=mock_ticker):
        assert market.analise_mercado_unificado("AAA") is None


def test_analise_carteira():
    with patch("investimentos_api.app.services.market.analise_mercado",
               return_value={"retorno_anualizado": 0.1}):
        result = market.analise_carteira([("AAA", 100)])
        assert result["total_investido"] == 100

    assert market.analise_carteira([])["total_investido"] == 0


# =====================================================
# RENTABILIDADE
# =====================================================

def test_renda_fixa_service():
    result = renda_fixa_service.calcular_renda_fixa(
        1000,
        datetime.utcnow()
    )
    assert "valor_atual" in result


def test_rentabilidade_fluxos():
    inv_rf = {
        "tipo_investimento": "RENDA_FIXA",
        "valor_investido": 1000,
        "data_aplicacao": "2024-01-01T00:00:00",
        "ticker": None
    }
    assert "valor_atual" in rentabilidade_service.calcular_rentabilidade(inv_rf)

    inv_acoes = {
        "tipo_investimento": "ACOES",
        "valor_investido": 100,
        "data_aplicacao": "2024-01-01T00:00:00",
        "ticker": "AAA"
    }

    with patch("investimentos_api.app.services.rentabilidade_service.analise_mercado",
               return_value={"retorno_acumulado": 0.1}):
        result = rentabilidade_service.calcular_rentabilidade(inv_acoes)
        assert result["rentabilidade_percentual"] == 10.0

    with patch("investimentos_api.app.services.rentabilidade_service.analise_mercado",
               side_effect=Exception):
        result = rentabilidade_service.calcular_rentabilidade(inv_acoes)
        assert result["rentabilidade_percentual"] == 0.0
import pandas as pd
from typing import List, Tuple, Dict
import yfinance as yf
import numpy as np


def _download_close(ticker: str):
    data = yf.download(ticker, period="1y")
    if data.empty:
        raise ValueError(f"Sem histórico para {ticker}")


    if "Close" in data.columns and not isinstance(data["Close"], pd.DataFrame):
        return data["Close"]


    if "Close" in data.columns and isinstance(data["Close"], pd.DataFrame):

        return data["Close"].iloc[:, 0]

    if isinstance(data.columns, pd.MultiIndex):

        try:
            close = data.xs("Close", level=1, axis=1)
            if isinstance(close, pd.DataFrame):
                return close.iloc[:, 0]
            return close
        except Exception:
            pass

    raise ValueError(f"Não foi possível encontrar coluna Close para {ticker}")



def analise_mercado(ticker: str) -> Dict:
    close = _download_close(ticker)
    retorno_acumulado = (close.iloc[-1] / close.iloc[0]) - 1
    retorno_anualizado = (1 + retorno_acumulado) ** (252 / len(close)) - 1
    volatilidade_anualizada = close.pct_change().std() * (252 ** 0.5)

    return {
        "ticker": ticker,
        "retorno_acumulado": float(retorno_acumulado),
        "retorno_anualizado": float(retorno_anualizado),
        "volatilidade_anualizada": float(volatilidade_anualizada),
    }



def analise_mercado_unificado(ticker: str):
    ticker = ticker.strip().upper()

    tentativas = [ticker]

    if not ticker.endswith(".SA"):
        tentativas.append(f"{ticker}.SA")

    if ticker.endswith(".SA"):
        tentativas.append(ticker.replace(".SA", ""))

    for tk in tentativas:
        try:
            ativo = yf.Ticker(tk)
            hist = ativo.history(period="1y")

            if hist.empty:
                continue

            close = hist["Close"]

            preco_atual = float(close.iloc[-1])
            preco_inicial = float(close.iloc[0])

            variacao_percentual = (preco_atual / preco_inicial) - 1
            retorno_acumulado = variacao_percentual

            dias = len(close)
            retorno_anualizado = (1 + retorno_acumulado) ** (365 / dias) - 1

            volatilidade_anualizada = float(close.pct_change().std() * np.sqrt(252))

            return {
                "ticker": tk,
                "preco_atual": preco_atual,
                "retorno_acumulado": float(retorno_acumulado),
                "retorno_anualizado": float(retorno_anualizado),
                "variacao_percentual": float(variacao_percentual),
                "volatilidade_anualizada": float(volatilidade_anualizada),
            }


        except Exception:
            continue

    return None




def analise_carteira(itens: List[Tuple[str, float]]) -> Dict:
    if not itens:
        return {
            "itens": [],
            "retorno_ponderado_anualizado": 0.0,
            "total_investido": 0.0,
        }

    total = sum(v for _, v in itens if v and v > 0)
    saida_itens = []
    retorno_ponderado = 0.0

    for tk, valor in itens:
        if not tk or not valor or valor <= 0:
            continue

        try:
            m = analise_mercado(tk)
        except Exception:
            # ticker inválido → ignora
            continue

        peso = float(valor) / total if total > 0 else 0.0
        retorno_ponderado += peso * m["retorno_anualizado"]

        saida_itens.append({
            "ticker": tk,
            "peso": peso,
            **m,
        })

    if not saida_itens:
        return {
            "itens": [],
            "retorno_ponderado_anualizado": 0.0,
            "total_investido": total,
        }

    return {
        "itens": saida_itens,
        "retorno_ponderado_anualizado": retorno_ponderado,
        "total_investido": total,
    }

from datetime import datetime
from .renda_fixa_service import calcular_renda_fixa
from .market import analise_mercado

def calcular_rentabilidade(investimento: dict):


    print("DEBUG tipo:", investimento.get("tipo_investimento"))
    print("DEBUG ticker:", investimento.get("ticker"))
    print("DEBUG data:", investimento.get("data_aplicacao"))

    tipo = investimento["tipo_investimento"]
    valor_inicial = investimento["valor_investido"]
    data_aplicacao = investimento["data_aplicacao"]
    ticker = investimento.get("ticker")


    if isinstance(data_aplicacao, str):
        data_aplicacao = datetime.fromisoformat(data_aplicacao.replace("Z", ""))


    if tipo == "RENDA_FIXA":
        return calcular_renda_fixa(
            valor_inicial=valor_inicial,
            data_aplicacao=data_aplicacao,
            percentual_cdi=1.1
        )


    if ticker:
        try:
            m = analise_mercado(ticker)
            retorno = m["retorno_acumulado"]
            valor_atual = valor_inicial * (1 + retorno)
            return {
                "valor_atual": round(valor_atual, 2),
                "rentabilidade_percentual": round(retorno * 100, 4),
                "dias_corridos": None
            }
        except Exception:
            return {
                "valor_atual": valor_inicial,
                "rentabilidade_percentual": 0.0,
                "dias_corridos": None
            }


    return {
        "valor_atual": valor_inicial,
        "rentabilidade_percentual": 0.0,
        "dias_corridos": None
    }

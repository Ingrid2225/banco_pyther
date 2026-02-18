from datetime import datetime

CDI_DIARIO = 0.0003

def calcular_renda_fixa(valor_inicial: float, data_aplicacao: datetime, percentual_cdi: float = 1.0):


    hoje = datetime.utcnow()
    dias = (hoje - data_aplicacao).days or 1

    taxa_diaria = CDI_DIARIO * percentual_cdi
    valor_atual = valor_inicial * ((1 + taxa_diaria) ** dias)
    rentabilidade = (valor_atual / valor_inicial) - 1

    return {
        "valor_atual": round(valor_atual, 2),
        "rentabilidade_percentual": round(rentabilidade * 100, 4),
        "dias_corridos": dias
    }

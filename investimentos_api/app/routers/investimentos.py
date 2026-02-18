from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from ..services.data_client import DataClient
from ..services.market import analise_mercado_unificado
from ..schemas import (
    InvestimentoCreate,
    AporteCreate,
    ResgateParcialCreate,
    ResgateTotalCreate,
    ProjecaoPatrimonioOut,
    CarteiraOut,
    InvestimentoOut,
)

router = APIRouter(prefix="/investimentos", tags=["investimentos"])

CDI_DIARIO = 0.00036


def _err(status_code: int, code: str, message: str):
    return HTTPException(
        status_code=status_code,
        detail={"status": status_code, "code": code, "message": message},
    )


async def get_dc() -> DataClient:
    return DataClient()


@router.get("/analise/{ticker}")
async def analise_ticker(ticker: str):
    analise = analise_mercado_unificado(ticker)
    if analise is None:
        return {"ticker": ticker, "mensagem": "Sem histórico disponível para este ativo"}
    return analise


@router.get("/carteira/{agencia}/{numero_conta}", response_model=CarteiraOut)
async def analise_carteira(agencia: str, numero_conta: str, dc: DataClient = Depends(get_dc)):
    conta = await dc.get_conta(agencia, numero_conta)
    if not conta:
        raise _err(404, "CONTA_NAO_ENCONTRADA", "Conta não existe")

    investimentos = await dc.list_investimentos_por_conta(agencia, numero_conta)

    itens = []
    total_investido = 0.0
    for inv in investimentos:
        analise = analise_mercado_unificado(inv["ticker"]) if inv["ticker"] else None
        itens.append({
            "ticker": inv["ticker"],
            "tipo_investimento": inv["tipo_investimento"],
            "valor_investido": inv["valor_investido"],
            "retorno_acumulado": analise["retorno_acumulado"] if analise else 0.0,
            "retorno_anualizado": analise["retorno_anualizado"] if analise else 0.0,
            "volatilidade_anualizada": analise["volatilidade_anualizada"] if analise else 0.0,
            "peso_na_carteira": (inv["valor_investido"] / total_investido) if total_investido > 0 else 0.0
        })
        total_investido += inv["valor_investido"]

    retorno_ponderado_anualizado = sum(
        item["retorno_anualizado"] * item["peso_na_carteira"] for item in itens
    )

    return {
        "agencia": agencia,
        "numero_conta": numero_conta,
        "total_investido": total_investido,
        "retorno_ponderado_anualizado": retorno_ponderado_anualizado,
        "itens": itens
    }


@router.get("/projecao/{agencia}/{numero_conta}", response_model=ProjecaoPatrimonioOut)
async def projecao_patrimonio(agencia: str, numero_conta: str, dc: DataClient = Depends(get_dc)):
    conta = await dc.get_conta(agencia, numero_conta)
    if not conta:
        raise _err(404, "CONTA_NAO_ENCONTRADA", "Conta não existe")

    investimentos = await dc.list_investimentos_por_conta(agencia, numero_conta)

    total_investido = sum(i["valor_investido"] for i in investimentos)
    patrimonio_atual = total_investido
    taxa_utilizada = 0.10
    patrimonio_projetado = patrimonio_atual * (1 + taxa_utilizada)
    patrimonio_projetado_anual = patrimonio_atual * (1 + taxa_utilizada)

    acoes = sum(i["valor_investido"] for i in investimentos if i["tipo_investimento"] == "ACOES")
    renda_fixa = sum(i["valor_investido"] for i in investimentos if i["tipo_investimento"] in ["RENDA_FIXA", "TESOURO"])

    if total_investido > 0:
        if renda_fixa / total_investido > 0.7:
            perfil_investidor = "CONSERVADOR"
        elif acoes / total_investido > 0.7:
            perfil_investidor = "ARROJADO"
        else:
            perfil_investidor = "MODERADO"
    else:
        perfil_investidor = "MODERADO"

    return {
        "agencia": agencia,
        "numero_conta": numero_conta,
        "total_investido": total_investido,
        "patrimonio_atual": patrimonio_atual,
        "patrimonio_projetado": patrimonio_projetado,
        "patrimonio_projetado_anual": patrimonio_projetado_anual,
        "taxa_utilizada": taxa_utilizada,
        "perfil_investidor": perfil_investidor,
        "investimentos": investimentos
    }


@router.post("/{agencia}/{numero_conta}", response_model=InvestimentoOut)
async def aplicar(agencia: str, numero_conta: str, payload: InvestimentoCreate, dc: DataClient = Depends(get_dc)):
    conta = await dc.get_conta(agencia, numero_conta)
    if not conta:
        raise _err(404, "CONTA_NAO_ENCONTRADA", "Conta não existe")

    investimento_payload = payload.dict()
    investimento_payload["agencia"] = agencia
    investimento_payload["numero_conta"] = numero_conta

    investimento = await dc.create_investimento(investimento_payload)
    return investimento


@router.post("/{agencia}/{numero_conta}/aporte", response_model=InvestimentoOut, status_code=status.HTTP_201_CREATED)
async def aporte(agencia: str, numero_conta: str, body: AporteCreate, dc: DataClient = Depends(get_dc)):
    conta = await dc.get_conta(agencia, numero_conta)
    if not conta:
        raise _err(404, "CONTA_NAO_ENCONTRADA", "Conta não existe")

    payload = body.model_dump()
    payload["agencia"] = agencia
    payload["numero_conta"] = numero_conta

    investimento = await dc.create_investimento(payload)
    return investimento


@router.post("/{agencia}/{numero_conta}/resgatar", response_model=InvestimentoOut)
async def resgate_parcial(agencia: str, numero_conta: str, body: ResgateParcialCreate, dc: DataClient = Depends(get_dc)):
    conta = await dc.get_conta(agencia, numero_conta)
    if not conta:
        raise _err(404, "CONTA_NAO_ENCONTRADA", "Conta não existe")

    investimentos = await dc.list_investimentos_por_conta(agencia, numero_conta)

    investimento = next((i for i in investimentos if i["ticker"] == body.ticker and i["ativo"]), None)
    if not investimento:
        raise _err(404, "INVESTIMENTO_NAO_ENCONTRADO", "Investimento não encontrado")

    if body.valor_resgate > investimento["valor_investido"]:
        raise _err(422, "RESGATE_MAIOR_QUE_SALDO", "Valor de resgate excede o investido")

    novo_valor = investimento["valor_investido"] - body.valor_resgate

    if novo_valor == 0:
        atualizado = await dc.resgate_total(agencia, numero_conta, body.ticker)
    else:
        atualizado = await dc.update_investimento(investimento["id"], {"valor_investido": novo_valor})

    return atualizado


@router.post("/{agencia}/{numero_conta}/resgatar_total", response_model=InvestimentoOut)
async def resgate_total(agencia: str, numero_conta: str, body: ResgateTotalCreate, dc: DataClient = Depends(get_dc)):
    conta = await dc.get_conta(agencia, numero_conta)
    if not conta:
        raise _err(404, "CONTA_NAO_ENCONTRADA", "Conta não existe")

    investimentos = await dc.list_investimentos_por_conta(agencia, numero_conta)

    investimento = next((i for i in investimentos if i["ticker"] == body.ticker and i["ativo"]), None)
    if not investimento:
        raise _err(404, "INVESTIMENTO_NAO_ENCONTRADO", "Investimento não encontrado")

    atualizado = await dc.resgate_total(agencia, numero_conta, body.ticker)
    return atualizado


@router.get("/{agencia}/{numero_conta}", response_model=List[InvestimentoOut])
async def list_investimentos_por_conta(agencia: str, numero_conta: str, dc: DataClient = Depends(get_dc)):
    investimentos = await dc.list_investimentos_por_conta(agencia, numero_conta)
    return investimentos


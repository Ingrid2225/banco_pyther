from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from ..db import get_db
from ..models import Investimento, Conta
from ..schemas import (
    InvestimentoCreate,
    InvestimentoOut,
)

router = APIRouter(prefix="/internal/investimentos", tags=["investimentos_db"])


def _err(status_code: int, code: str, message: str):
    return HTTPException(
        status_code=status_code,
        detail={"status": status_code, "code": code, "message": message},
    )


@router.get("", summary="Listar todos os investimentos")
def listar_todos_investimentos(db: Session = Depends(get_db)):
    return db.query(Investimento).all()


@router.post("", response_model=InvestimentoOut)
async def create_investimento(body: InvestimentoCreate, db: Session = Depends(get_db)):

    # 🔎 Buscar conta
    conta = (
        db.query(Conta)
        .filter(
            Conta.agencia == body.agencia,
            Conta.numero_conta == body.numero_conta
        )
        .first()
    )

    if not conta:
        raise _err(404, "CONTA_NAO_ENCONTRADA", "Conta não encontrada")

    # ✅ Criar investimento vinculado corretamente
    investimento = Investimento(
        agencia=body.agencia,
        numero_conta=body.numero_conta,
        tipo_investimento=body.tipo_investimento,
        valor_investido=body.valor_investido,
        ticker=body.ticker,
        rentabilidade=body.rentabilidade,
        ativo=body.ativo,
        data_aplicacao=body.data_aplicacao,
        conta_id=conta.id   # 🔥 ESSA LINHA RESOLVE TUDO
    )

    db.add(investimento)
    db.commit()
    db.refresh(investimento)

    return investimento

@router.get("/conta/{agencia}/{numero_conta}", response_model=list[InvestimentoOut])
def listar_por_conta(agencia: str, numero_conta: str, db: Session = Depends(get_db)):
    investimentos = (
        db.query(Investimento)
        .filter(
            Investimento.agencia == agencia,
            Investimento.numero_conta == numero_conta
        )
        .all()
    )
    return investimentos


@router.put("/{agencia}/{numero_conta}/resgate_total/{ticker}", response_model=InvestimentoOut)
def resgate_total_interno(
    agencia: str,
    numero_conta: str,
    ticker: str,
    db: Session = Depends(get_db)
):
    investimento = (
        db.query(Investimento)
        .filter(
            Investimento.agencia == agencia,
            Investimento.numero_conta == numero_conta,
            Investimento.ticker == ticker,
            Investimento.ativo == True
        )
        .first()
    )

    if not investimento:
        raise HTTPException(
            status_code=404,
            detail={
                "status": 404,
                "code": "INVESTIMENTO_NAO_ENCONTRADO",
                "message": "Nenhum investimento ativo encontrado para esse ticker"
            }
        )

    investimento.valor_investido = 0
    investimento.ativo = False

    db.commit()
    db.refresh(investimento)

    return investimento

@router.put("/{investimento_id}", response_model=InvestimentoOut)
def atualizar_investimento(
    investimento_id: UUID,
    payload: dict,
    db: Session = Depends(get_db)
):
    investimento = (
        db.query(Investimento)
        .filter(Investimento.id == investimento_id)
        .first()
    )

    if not investimento:
        raise HTTPException(
            status_code=404,
            detail={
                "status": 404,
                "code": "INVESTIMENTO_NAO_ENCONTRADO",
                "message": "Investimento não encontrado"
            }
        )

    for campo, valor in payload.items():
        setattr(investimento, campo, valor)

    db.commit()
    db.refresh(investimento)

    return investimento
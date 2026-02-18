from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from uuid import UUID

from ..db import get_db
from ..models import Conta
from ..schemas import (
    ContaCreate,
    ContaUpdate,
    ContaOut,
    OperacaoPorChaves,
    ChequeEspecialCadastro,
    InvestimentoOut
)

router = APIRouter(prefix="/contas", tags=["contas"])

def _err(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"status": status_code, "code": code, "message": message},
    )

def _get_by_id_or_404(db: Session, id_: UUID) -> Conta:
    conta = db.get(Conta, id_)
    if not conta:
        raise _err(404, "CONTA_NAO_ENCONTRADA", "Conta não encontrada")
    return conta

def _get_by_agencia_numero_or_404(db: Session, agencia: str, numero_conta: str) -> Conta:
    conta = (
        db.query(Conta)
        .filter(and_(Conta.agencia == agencia, Conta.numero_conta == numero_conta))
        .first()
    )
    if not conta:
        raise _err(404, "CONTA_NAO_ENCONTRADA", "Conta não encontrada")
    return conta

def _to_out(c: Conta) -> dict:
    if c.cheque_especial_contratado and c.saldo_cc < 0:
        limite_atual = max(0.0, c.limite_cheque_especial + c.saldo_cc)
    else:
        limite_atual = c.limite_cheque_especial

    return {
        "id": str(c.id),  # garante serialização UUID
        "agencia": str(c.agencia),
        "numero_conta": str(c.numero_conta),
        "nome": str(c.nome),
        "cpf": str(c.cpf),
        "telefone": str(c.telefone),
        "email": str(c.email) if c.email else "teste@teste.com",  # fallback
        "perfil_investidor": c.perfil_investidor or "MODERADO",   # enum default
        "correntista": bool(c.correntista),
        "saldo_cc": float(c.saldo_cc or 0.0),
        "cheque_especial_contratado": bool(c.cheque_especial_contratado),
        "limite_cheque_especial": float(c.limite_cheque_especial or 0.0),
        "limite_atual": float(limite_atual or 0.0),
    }

@router.get("/internal/id_por_agencia_conta")
def obter_id_por_agencia_conta(agencia: str, numero_conta: str, db: Session = Depends(get_db)):
    conta = (
        db.query(Conta)
        .filter(
            Conta.agencia == agencia,
            Conta.numero_conta == numero_conta
        )
        .first()
    )

    if not conta:
        raise HTTPException(
            status_code=404,
            detail={
                "status": 404,
                "code": "CONTA_NAO_ENCONTRADA",
                "message": "Conta não encontrada"
            }
        )

    return {"id": conta.id}

@router.post("", response_model=ContaOut, status_code=status.HTTP_201_CREATED, summary="Criar conta")
def criar_conta(body: ContaCreate, db: Session = Depends(get_db)):
    saldo_inicial = body.saldo_cc or 0.0
    if saldo_inicial < 0:
        raise _err(422, "SALDO_NEGATIVO_INICIAL", "Não pode criar cliente com saldo negativo")

    if body.correntista is False and saldo_inicial != 0:
        raise _err(422, "SALDO_INVALIDO_CORRENTISTA_FALSE", "Conta não pode ter saldo se correntista=False")

    if body.cheque_especial_contratado:
        if body.limite_cheque_especial is None or body.limite_cheque_especial < 0:
            raise _err(422, "LIMITE_CHEQUE_ESPECIAL_INVALIDO", "Limite deve ser >= 0 ao habilitar cheque especial")

    existente_ag_num = (
        db.query(Conta)
        .filter(and_(Conta.agencia == body.agencia, Conta.numero_conta == body.numero_conta))
        .first()
    )
    if existente_ag_num:
        raise _err(409, "CONTA_DUPLICADA", "Conta já existe para essa agência e número")

    existente_cpf = db.query(Conta).filter(Conta.cpf == body.cpf).first()
    if existente_cpf:
        raise _err(409, "CPF_JA_CADASTRADO", "Já existe uma conta cadastrada para este CPF.")

    conta = Conta(**body.model_dump())
    try:
        db.add(conta)
        db.commit()
        db.refresh(conta)
    except IntegrityError:
        db.rollback()
        raise _err(409, "CONFLITO_UNICO", "Agência/número ou CPF já cadastrado.")

    return _to_out(conta)

@router.get("", response_model=list[ContaOut], summary="Listar todas as contas")
def listar_contas(db: Session = Depends(get_db)):
    contas = db.query(Conta).all()
    return [_to_out(c) for c in contas]

@router.get("/{agencia}/{numero_conta}", response_model=ContaOut)
def get_conta(agencia: str, numero_conta: str, db: Session = Depends(get_db)):
    conta = (
        db.query(Conta)
        .filter(Conta.agencia == agencia, Conta.numero_conta == numero_conta)
        .first()
    )
    if not conta:
        raise HTTPException(
            status_code=404,
            detail={"status": 404, "code": "CONTA_NAO_ENCONTRADA", "message": "Conta não existe"}
        )
    return _to_out(conta)

@router.put("/{agencia}/{numero_conta}", response_model=ContaOut, summary="Atualizar conta por agência/número")
def atualizar_conta(agencia: str, numero_conta: str, body: ContaUpdate, db: Session = Depends(get_db)):
    conta = _get_by_agencia_numero_or_404(db, agencia, numero_conta)
    if body.correntista is False and conta.saldo_cc != 0:
        raise _err(422, "SALDO_INVALIDO_CORRENTISTA_FALSE", "Conta correntista=False deve ter saldo 0")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(conta, field, value)

    try:
        db.commit()
        db.refresh(conta)
    except IntegrityError:
        db.rollback()
        raise _err(409, "CONFLITO_UNICO", "Dados atualizados violam restrição de unicidade (CPF).")

    return _to_out(conta)

@router.delete("/{agencia}/{numero_conta}/desativar", status_code=status.HTTP_204_NO_CONTENT)
def desativar_conta(agencia: str, numero_conta: str, db: Session = Depends(get_db)):
    conta = _get_by_agencia_numero_or_404(db, agencia, numero_conta)

    if float(conta.saldo_cc) != 0.0:
        raise _err(409, "SALDO_NAO_ZERADO", "Só é possível desativar conta com saldo zerado")

    if conta.investimentos:
        raise _err(409, "CONTA_COM_INVESTIMENTOS", "Não é possível desativar conta com investimentos vinculados")

    db.delete(conta)
    db.commit()
    return None

@router.post("/operacoes/depositar", response_model=ContaOut, summary="Depositar")
def depositar(body: OperacaoPorChaves, db: Session = Depends(get_db)):
    conta = _get_by_agencia_numero_or_404(db, body.agencia, body.numero_conta)
    conta.saldo_cc += body.valor
    db.commit()
    db.refresh(conta)
    return _to_out(conta)



@router.post("/operacoes/sacar", response_model=ContaOut, summary="Sacar")
def sacar(body: OperacaoPorChaves, db: Session = Depends(get_db)):
    conta = _get_by_agencia_numero_or_404(db, body.agencia, body.numero_conta)
    valor = body.valor
    novo_saldo = conta.saldo_cc - valor

    if novo_saldo >= 0:
        conta.saldo_cc = novo_saldo
        db.commit()
        db.refresh(conta)
        return _to_out(conta)

    if not conta.cheque_especial_contratado:
        raise _err(409, "SALDO_INSUFICIENTE", "Saldo insuficiente")

    if novo_saldo < -conta.limite_cheque_especial:
        raise _err(409, "CHEQUE_ESPECIAL_EXCEDIDO", "Limite do cheque especial excedido")

    conta.saldo_cc = novo_saldo
    db.commit()
    db.refresh(conta)
    return _to_out(conta)



@router.put("/{id}/cheque_especial/cadastrar", response_model=ContaOut, summary="Cadastrar cheque especial por ID")
def cadastrar_cheque_especial(id: UUID, body: ChequeEspecialCadastro, db: Session = Depends(get_db)):
    conta = _get_by_id_or_404(db, id)
    if body.habilitado is False and conta.saldo_cc < 0:
        raise _err(409, "CHEQUE_ESPECIAL_COM_SALDO_NEGATIVO", "Não pode desabilitar cheque especial com saldo negativo")
    if body.habilitado is True and body.limite < 0:
        raise _err(422, "LIMITE_INVALIDO", "Limite deve ser >= 0")

    conta.cheque_especial_contratado = body.habilitado
    conta.limite_cheque_especial = body.limite
    db.commit()
    db.refresh(conta)
    return _to_out(conta)


@router.get("/internal/investimentos/conta/{agencia}/{numero_conta}", response_model=list[InvestimentoOut])
def listar_investimentos_por_conta(agencia: str, numero_conta: str, db: Session = Depends(get_db)):
    conta = _get_by_agencia_numero_or_404(db, agencia, numero_conta)
    return [
        {
            "id": inv.id,  # UUID já bate com InvestimentoOut
            "agencia": inv.agencia,
            "numero_conta": inv.numero_conta,
            "tipo_investimento": inv.tipo_investimento,
            "valor_investido": float(inv.valor_investido),
            "ticker": inv.ticker,
            "ativo": bool(inv.ativo),
            "data_aplicacao": inv.data_aplicacao,  # datetime já bate com InvestimentoOut
        }
        for inv in conta.investimentos
    ]



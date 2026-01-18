
from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError, RequestError
from typing import List
import os

from ..services.db_conta import DbConta
from ..services.models import ContaModel
from ..services.schemas import (
    ContaCreateIn,
    ContaUpdateIn,
    OperacaoPorChavesIn,
    ChequeEspecialCadastroIn
)

router = APIRouter(prefix="/contas", tags=["contas"])


def get_db() -> DbConta:
    base_url = os.getenv("CLIENTES_DB_URL", "http://localhost:8001")
    return DbConta(base_url=base_url)


def _safe_detail(e: HTTPStatusError) -> dict:

    try:
        payload = e.response.json()
        detail = payload.get("detail")

        if isinstance(detail, dict):
            return detail

        if isinstance(detail, str):
            return {
                "status": e.response.status_code,
                "code": "ERRO_CLIENTES_DB",
                "message": detail
            }

        return {
            "status": e.response.status_code,
            "code": "ERRO_CLIENTES_DB",
            "message": "Erro no serviço clientes_db"
        }
    except Exception:
        return {
            "status": e.response.status_code,
            "code": "ERRO_CLIENTES_DB",
            "message": "Erro no serviço clientes_db"
        }


def _raise_unavailable():
    raise HTTPException(
        status_code=503,
        detail={
            "status": 503,
            "code": "CLIENTES_DB_INDISPONIVEL",
            "message": "clientes_db indisponível"
        }
    )


@router.post(
    "",
    response_model=ContaModel,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Conta"
)
async def criar_conta(body: ContaCreateIn, db: DbConta = Depends(get_db)):
    try:
        return await db.criar_conta(body.model_dump(by_alias=True))
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))
    except RequestError:
        _raise_unavailable()


@router.get("", response_model=List[ContaModel], summary="Listar Contas")
async def listar_contas(db: DbConta = Depends(get_db)):
    try:
        return await db.listar_contas()
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))
    except RequestError:
        _raise_unavailable()


@router.get(
    "/{agencia}/{numero_conta}",
    response_model=ContaModel,
    summary="Obter Conta"
)
async def obter_conta(agencia: str, numero_conta: str, db: DbConta = Depends(get_db)):
    try:
        return await db.obter_conta(agencia, numero_conta)
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))
    except RequestError:
        _raise_unavailable()

@router.put(
    "/{agencia}/{numero_conta}",
    response_model=ContaModel,
    summary="Atualizar Conta"
)
async def atualizar_conta(
    agencia: str,
    numero_conta: str,
    body: ContaUpdateIn,
    db: DbConta = Depends(get_db)
):
    try:
        return await db.atualizar_conta(
            agencia, numero_conta, body.model_dump(exclude_unset=True)
        )
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))
    except RequestError:
        _raise_unavailable()

@router.delete(
    "/{agencia}/{numero_conta}/desativar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar conta"
)
async def desativar_conta(agencia: str, numero_conta: str, db: DbConta = Depends(get_db)):


    try:
        conta = await db.obter_conta(agencia, numero_conta)
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))
    except RequestError:
        _raise_unavailable()

    saldo = float(conta.get("saldo_cc", 0.0))

    if saldo != 0.0:
        raise HTTPException(
            status_code=409,
            detail={
                "status": 409,
                "code": "SALDO_NAO_ZERADO",
                "message": "Só é possível desativar conta com saldo zerado"
            }
        )

    try:
        await db.desativar_conta(agencia, numero_conta)
        return None
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))


@router.post(
    "/operacoes/depositar",
    response_model=ContaModel,
    summary="Depositar"
)
async def depositar(body: OperacaoPorChavesIn, db: DbConta = Depends(get_db)):
    try:
        return await db.depositar(body.model_dump(by_alias=True))
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))
    except RequestError:
        _raise_unavailable()


@router.post(
    "/operacoes/sacar",
    response_model=ContaModel,
    summary="Sacar"
)
async def sacar(body: OperacaoPorChavesIn, db: DbConta = Depends(get_db)):
    try:
        return await db.sacar(body.model_dump(by_alias=True))
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))
    except RequestError:
        _raise_unavailable()


@router.put(
    "/{agencia}/{numero_conta}/cheque_especial/cadastrar",
    response_model=ContaModel,
    summary="Cadastrar/Ajustar cheque especial"
)
async def cadastrar_cheque_especial_gateway(
    agencia: str,
    numero_conta: str,
    body: ChequeEspecialCadastroIn,
    db: DbConta = Depends(get_db)
):

    try:
        conta_db = await db.obter_conta(agencia, numero_conta)
        id_ = conta_db["id"]
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))
    except RequestError:
        _raise_unavailable()

    payload = {
        "agencia": agencia,
        "numero_conta": numero_conta,
        "habilitado": body.habilitado,
        "limite": body.limite
    }

    try:
        return await db.cadastrar_cheque_especial(id_, payload)
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))
    except RequestError:
        _raise_unavailable()


@router.get(
    "/{agencia}/{numero_conta}/score_credito",
    summary="Score de crédito"
)
async def calcular_score_gateway(
    agencia: str,
    numero_conta: str,
    db: DbConta = Depends(get_db)
):
    try:
        conta = await db.obter_conta(agencia, numero_conta)
    except HTTPStatusError as e:
        raise HTTPException(e.response.status_code, _safe_detail(e))

    saldo = float(conta["saldo_cc"])
    score = 0.0 if saldo < 0 else round(saldo * 0.1, 4)

    return {
        "agencia": agencia,
        "numero_conta": numero_conta,
        "score_credito": score
    }

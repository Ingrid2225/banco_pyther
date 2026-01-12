from fastapi import APIRouter, Depends, HTTPException, status
from httpx import HTTPStatusError, RequestError
from typing import List
import os
from ..schemas import ClienteCreate, ClienteUpdate, ClienteOut
from ..services.db_client import DbClient

router = APIRouter(prefix="/clientes", tags=["clientes"])


def get_db() -> DbClient:


    base_url = os.getenv("CLIENTES_DB_URL", "http://localhost:8001")
    return DbClient(base_url=base_url)



@router.post(
    "",
    response_model=ClienteOut,
    status_code=status.HTTP_201_CREATED,
    responses={

        422: {
            "description": "Saldo negativo na criação",
            "content": {"application/json": {
                "example": {"detail": "cliente inválido, não pode criar conta com saldo negativo"}}},
        }
    },
)
async def create_cliente(body: ClienteCreate, db: DbClient = Depends(get_db)):

    saldo = body.saldo_cc if body.saldo_cc is not None else 0.0


    if saldo < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="cliente inválido, não pode criar conta com saldo negativo",
        )


    payload = body.model_dump() if hasattr(body, "model_dump") else body.dict()
    payload["saldo_cc"] = float(saldo)

    try:
        cliente_raw = await db.create_cliente(payload)
    except HTTPStatusError as e:

        if e.response.status_code == 422:

            try:
                detail = e.response.json().get("detail", None)
            except Exception:
                detail = None
            raise HTTPException(
                status_code=422,
                detail=detail or "cliente inválido, não pode criar conta com saldo negativo",
            )


        try:
            detail = e.response.json().get("detail", None)
        except Exception:
            detail = None
        raise HTTPException(status_code=502, detail=detail or "Erro no serviço clientes_db")
    except RequestError:

        raise HTTPException(status_code=503, detail="clientes_db indisponível")


    if isinstance(cliente_raw, dict):
        cliente_dict = cliente_raw
    elif hasattr(cliente_raw, "model_dump"):
        cliente_dict = cliente_raw.model_dump()
    elif hasattr(cliente_raw, "dict"):
        cliente_dict = cliente_raw.dict()
    else:
        cliente_dict = dict(cliente_raw)

    return {**cliente_dict, "score_credito": 0.0}


@router.get(
    "/{id}",
    response_model=ClienteOut,
    responses={
        404: {"description": "Cliente não encontrado"},
        502: {"description": "Erro no serviço clientes_db"},
        503: {"description": "clientes_db indisponível"},
    },
)
async def get_cliente(id: int, db: DbClient = Depends(get_db)):
    try:
        cliente = await db.get_cliente(id)
    except HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", None)
        except Exception:
            detail = None

        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=detail or "Cliente não encontrado")
        raise HTTPException(status_code=502, detail=detail or "Erro no serviço clientes_db")
    except RequestError:
        raise HTTPException(status_code=503, detail="clientes_db indisponível")

    return {**cliente, "score_credito": 0.0}


@router.get(
    "",
    response_model=List[ClienteOut],
    responses={
        502: {"description": "Erro no serviço clientes_db"},
        503: {"description": "clientes_db indisponível"},
    },
)
async def list_clientes(db: DbClient = Depends(get_db)):
    try:
        clientes = await db.list_clientes()
    except HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", None)
        except Exception:
            detail = None
        raise HTTPException(status_code=502, detail=detail or "Erro no serviço clientes_db")
    except RequestError:
        raise HTTPException(status_code=503, detail="clientes_db indisponível")

    return [{**c, "score_credito": 0.0} for c in clientes]


@router.put(
    "/{id}",
    response_model=ClienteOut,
    responses={
        400: {"description": "Regra de negócio (ex.: saldo negativo no update)"},
        404: {"description": "Cliente não encontrado"},
        422: {"description": "Payload inválido"},
        502: {"description": "Erro no serviço clientes_db"},
        503: {"description": "clientes_db indisponível"},
    },
)
async def update_cliente(id: int, body: ClienteUpdate, db: DbClient = Depends(get_db)):
    payload = (
        body.model_dump(exclude_unset=True)
        if hasattr(body, "model_dump")
        else body.dict(exclude_unset=True)
    )
    try:
        cliente = await db.update_cliente(id, payload)
    except HTTPStatusError as e:
        status_code = e.response.status_code
        try:
            detail = e.response.json().get("detail", None)
        except Exception:
            detail = None

        if status_code == 404:
            raise HTTPException(status_code=404, detail=detail or "Cliente não encontrado")
        if status_code == 400:
            raise HTTPException(status_code=400, detail=detail or "Saldo não pode ser negativo no update.")
        if status_code == 422:
            raise HTTPException(status_code=422, detail=detail or "Payload inválido")
        raise HTTPException(status_code=502, detail=detail or "Erro no serviço clientes_db")
    except RequestError:
        raise HTTPException(status_code=503, detail="clientes_db indisponível")

    return {**cliente, "score_credito": 0.0}


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"description": "Cliente não encontrado"},
        502: {"description": "Erro no serviço clientes_db"},
        503: {"description": "clientes_db indisponível"},
    },
)
async def delete_cliente(id: int, db: DbClient = Depends(get_db)):
    try:
        await db.delete_cliente(id)
    except HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", None)
        except Exception:
            detail = None

        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=detail or "Cliente não encontrado")
        raise HTTPException(status_code=502, detail=detail or "Erro no serviço clientes_db")
    except RequestError:
        raise HTTPException(status_code=503, detail="clientes_db indisponível")

    return None


@router.get(
    "/{id}/score_credito",
    summary="Calcula score (saldo_cc * 0,1)",
    responses={
        404: {"description": "Cliente não encontrado"},
        502: {"description": "Erro no serviço clientes_db"},
        503: {"description": "clientes_db indisponível"},
    },
)
async def calcular_score(id: int, db: DbClient = Depends(get_db)):

    try:
        cliente = await db.get_cliente(id)
    except HTTPStatusError as e:
        try:
            detail = e.response.json().get("detail", None)
        except Exception:
            detail = None

        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=detail or "Cliente não encontrado")
        raise HTTPException(status_code=502, detail=detail or "Erro no serviço clientes_db")
    except RequestError:
        raise HTTPException(status_code=503, detail="clientes_db indisponível")

    score = round(float(cliente["saldo_cc"]) * 0.1, 4)
    return {"cliente_id": id, "score_credito": score}
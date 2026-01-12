
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Cliente
from ..schemas import ClienteCreate, ClienteUpdate, ClienteOut

router = APIRouter(prefix="/clientes", tags=["clientes"])

@router.post(
    "",
    response_model=ClienteOut,
    status_code=status.HTTP_201_CREATED,
    responses={
        422: {
            "description": "Saldo negativo na criação",
            "content": {"application/json": {"example": {"detail": "cliente inválido, não pode criar conta com saldo negativo"}}},
        }
    },
)
def create_cliente(body: ClienteCreate, db: Session = Depends(get_db)):
    # saldo opcional; se não vier, assume 0.0 (cumpre NOT NULL + check constraint)
    saldo = 0.0 if body.saldo_cc is None else float(body.saldo_cc)

    # regra: nunca saldo negativo na criação → 422
    if saldo < 0.0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="cliente inválido, não pode criar conta com saldo negativo",
        )

    cliente = Cliente(
        nome=body.nome,
        telefone=body.telefone,
        correntista=body.correntista,
        saldo_cc=saldo,
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

@router.get("/{id}", response_model=ClienteOut)
def get_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return cliente

@router.get("", response_model=list[ClienteOut])
def list_clientes(db: Session = Depends(get_db)):
    return db.query(Cliente).all()

@router.put("/{id}", response_model=ClienteOut)
@router.patch("/{id}", response_model=ClienteOut)
def update_cliente(id: int, body: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    # Nome: atualiza se veio e não é placeholder
    if body.nome is not None and body.nome.strip() != "" and body.nome != "string":
        cliente.nome = body.nome

    # Telefone: atualiza se veio e não é 0 (placeholder)
    if body.telefone is not None and body.telefone != 0:
        cliente.telefone = body.telefone

    # Correntista: atualiza se veio
    if body.correntista is not None:
        cliente.correntista = body.correntista

    # Saldo: atualiza se veio e não-negativo
    if body.saldo_cc is not None:
        if body.saldo_cc < 0.0:
            raise HTTPException(status_code=400, detail="Saldo não pode ser negativo")
        cliente.saldo_cc = float(body.saldo_cc)

    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(cliente)
    db.commit()
    return None


# clientes_db/app/schemas.py
from pydantic import BaseModel, ConfigDict

class ClienteCreate(BaseModel):
    nome: str
    telefone: int
    correntista: bool
    saldo_cc: float | None = None

class ClienteUpdate(BaseModel):
    nome: str | None = None
    telefone: int | None = None
    correntista: bool | None = None
    saldo_cc: float | None = None

class ClienteOut(BaseModel):
    id: int
    nome: str
    telefone: int
    correntista: bool
    saldo_cc: float

    # 🔑 Necessário para serializar objetos ORM (SQLAlchemy) no Pydantic v2
    model_config = ConfigDict(from_attributes=True)

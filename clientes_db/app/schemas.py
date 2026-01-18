
from pydantic import BaseModel, Field, EmailStr, confloat, ConfigDict
from typing import Optional

class ContaCreate(BaseModel):
    agencia: str = Field(..., min_length=3, max_length=4, pattern=r"^\d{3,4}$")
    numero_conta: str = Field(..., min_length=4, max_length=8, pattern=r"^\d{4,8}$")

    nome: str = Field(..., min_length=2)
    cpf: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$")
    telefone: int = Field(..., ge=1000000000, le=99999999999)
    email: EmailStr

    correntista: bool = True
    saldo_cc: Optional[float] = Field(0.0)

    cheque_especial_contratado: bool = False
    limite_cheque_especial: Optional[float] = Field(0.0, ge=0)


class ContaUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: Optional[str] = None
    cpf: Optional[str] = Field(None, min_length=11, max_length=11, pattern=r"^\d{11}$")
    telefone: Optional[int] = Field(None, ge=1000000000, le=99999999999)
    email: Optional[EmailStr] = None
    correntista: Optional[bool] = None


class ContaOut(BaseModel):
    id: int
    agencia: str
    numero_conta: str

    nome: str
    cpf: str
    telefone: int
    email: EmailStr

    correntista: bool
    saldo_cc: float

    cheque_especial_contratado: bool
    limite_cheque_especial: float
    limite_atual: float
    score_credito: float


class OperacaoPorChaves(BaseModel):
    agencia: str = Field(..., min_length=3, max_length=4, pattern=r"^\d{3,4}$")
    numero_conta: str = Field(..., min_length=4, max_length=8, pattern=r"^\d{4,8}$")
    valor: confloat(gt=0) = Field(..., alias="saldo")


class ChequeEspecialCadastro(BaseModel):
    habilitado: bool
    limite: confloat(ge=0)

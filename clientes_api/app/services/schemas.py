from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, confloat, ConfigDict


class PerfilInvestidor(str, Enum):
    CONSERVADOR = "CONSERVADOR"
    MODERADO = "MODERADO"
    ARROJADO = "ARROJADO"


class ContaCreateIn(BaseModel):
    agencia: str = Field(..., min_length=3, max_length=4, pattern=r"^\d{3,4}$")
    numero_conta: str = Field(..., min_length=4, max_length=8, pattern=r"^\d{4,8}$")
    nome: str = Field(..., min_length=2)
    cpf: str = Field(..., min_length=11, max_length=11, pattern=r"^\d{11}$")
    telefone: str = Field(..., min_length=10, max_length=11, pattern=r"^\d{10,11}$")
    email: EmailStr
    perfil_investidor: PerfilInvestidor = PerfilInvestidor.MODERADO
    saldo_cc: float = 0.0
    correntista: bool = True
    cheque_especial_contratado: bool = False
    limite_cheque_especial: float = 0.0


class ContaUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: Optional[str] = None
    telefone: Optional[str] = Field(None, min_length=10, max_length=11, pattern=r"^\d{10,11}$")
    email: Optional[EmailStr] = None
    perfil_investidor: Optional[PerfilInvestidor] = None


class OperacaoPorChavesIn(BaseModel):
    agencia: str = Field(..., min_length=3, max_length=4, pattern=r"^\d{3,4}$")
    numero_conta: str = Field(..., min_length=4, max_length=8, pattern=r"^\d{4,8}$")
    valor: confloat(gt=0) = Field(..., alias="saldo")


class ChequeEspecialCadastroIn(BaseModel):
    habilitado: bool
    limite: confloat(ge=0)


class ContaModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    agencia: str
    numero_conta: str
    nome: str
    cpf: str
    telefone: str
    email: EmailStr
    perfil_investidor: PerfilInvestidor
    saldo_cc: float
    correntista: bool
    cheque_especial_contratado: bool
    limite_cheque_especial: float
    limite_atual: float
    score_credito: Optional[float] = None

from pydantic import BaseModel, EmailStr, Field, confloat
from uuid import UUID
from datetime import datetime
from enum import Enum
from typing import Optional


class PerfilInvestidor(str, Enum):
    CONSERVADOR = "CONSERVADOR"
    MODERADO = "MODERADO"
    ARROJADO = "ARROJADO"


class TipoInvestimento(str, Enum):
    RENDA_FIXA = "RENDA_FIXA"
    ACOES = "ACOES"
    FUNDOS = "FUNDOS"
    CRIPTO = "CRIPTO"


class ContaCreate(BaseModel):
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


class ContaUpdate(BaseModel):
    nome: Optional[str] = None
    cpf: Optional[str] = Field(None, min_length=11, max_length=11, pattern=r"^\d{11}$")
    telefone: Optional[str] = Field(None, min_length=10, max_length=11, pattern=r"^\d{10,11}$")
    email: Optional[EmailStr] = None
    perfil_investidor: Optional[PerfilInvestidor] = None
    correntista: Optional[bool] = None


class ContaOut(BaseModel):
    id: UUID
    agencia: str
    numero_conta: str
    nome: str
    cpf: str
    telefone: str
    email: EmailStr
    perfil_investidor: PerfilInvestidor
    correntista: bool
    saldo_cc: float
    cheque_especial_contratado: bool
    limite_cheque_especial: float
    limite_atual: float


class OperacaoPorChaves(BaseModel):
    agencia: str = Field(..., min_length=3, max_length=4, pattern=r"^\d{3,4}$")
    numero_conta: str = Field(..., min_length=4, max_length=8, pattern=r"^\d{4,8}$")
    valor: confloat(gt=0) = Field(..., alias="saldo")


class ChequeEspecialCadastro(BaseModel):
    habilitado: bool
    limite: confloat(ge=0)


class InvestimentoCreate(BaseModel):
    agencia: str
    numero_conta: str
    tipo_investimento: str
    valor_investido: float
    rentabilidade: float = 0.0
    ticker: Optional[str]
    ativo: bool
    data_aplicacao: datetime

class InvestimentoOut(BaseModel):
    id: UUID
    agencia: str
    numero_conta: str
    tipo_investimento: str
    valor_investido: float
    ticker: Optional[str]
    ativo: bool
    data_aplicacao: datetime


class InvestimentoOutPublic(BaseModel):
    tipo_investimento: TipoInvestimento
    valor_investido: float
    ticker: Optional[str]
    rentabilidade: float
    ativo: bool
    agencia: str
    numero_conta: str
    data_aplicacao: datetime

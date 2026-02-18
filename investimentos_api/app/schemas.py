from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class PerfilInvestidor(str, Enum):
    CONSERVADOR = "CONSERVADOR"
    MODERADO = "MODERADO"
    ARROJADO = "ARROJADO"


class TipoInvestimento(str, Enum):
    RENDA_FIXA = "RENDA_FIXA"
    ACOES = "ACOES"
    FUNDOS = "FUNDOS"
    CRIPTO = "CRIPTO"


class InvestimentoOut(BaseModel):
    id: UUID
    agencia: str
    numero_conta: str
    tipo_investimento: TipoInvestimento
    valor_investido: float
    rentabilidade: float = 0.0  # ✅ agora não é mais obrigatório
    ativo: bool
    ticker: Optional[str] = None
    data_aplicacao: datetime


class InvestimentoBase(BaseModel):
    tipo_investimento: TipoInvestimento
    valor_investido: float
    rentabilidade: float = 0.0
    ativo: bool = True
    ticker: Optional[str] = Field(
        default=None,
        description="Código do ativo (ex: PETR4.SA, AAPL, BTC-USD)"
    )


class InvestimentoCreate(BaseModel):
    tipo_investimento: TipoInvestimento
    valor_investido: float
    ticker: Optional[str] = None
    ativo: bool = True
    data_aplicacao: datetime


class InvestimentoOutPublic(InvestimentoBase):
    agencia: str
    numero_conta: str
    data_aplicacao: datetime


class AporteCreate(BaseModel):
    tipo_investimento: TipoInvestimento
    valor_investido: float
    ticker: Optional[str] = None
    rentabilidade: float = 0.0
    ativo: bool = True
    data_aplicacao: datetime


class ResgateParcialCreate(BaseModel):
    ticker: str
    valor_resgate: float


class ResgateTotalCreate(BaseModel):
    ticker: str


class MercadoOut(BaseModel):
    ticker: Optional[str] = None
    preco_atual: float
    retorno_acumulado: float
    retorno_anualizado: float
    variacao_percentual: float


class ItemCarteiraOut(BaseModel):
    ticker: Optional[str] = None
    tipo_investimento: TipoInvestimento
    valor_investido: float
    retorno_acumulado: float
    retorno_anualizado: float
    volatilidade_anualizada: float
    peso_na_carteira: float


class CarteiraOut(BaseModel):
    agencia: str
    numero_conta: str
    total_investido: float
    retorno_ponderado_anualizado: float
    itens: List[ItemCarteiraOut]


class ProjecaoPatrimonioOut(BaseModel):
    agencia: str
    numero_conta: str
    perfil_investidor: PerfilInvestidor
    patrimonio_atual: float
    patrimonio_projetado_anual: float
    taxa_utilizada: float


class PatrimonioOut(BaseModel):
    agencia: str
    numero_conta: str
    patrimonio_total: float
    total_investido: float
    saldo_disponivel: float
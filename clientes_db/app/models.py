import uuid
from sqlalchemy import (
    Column, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base

class Conta(Base):
    __tablename__ = "contas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agencia = Column(String(4), nullable=False)
    numero_conta = Column(String(8), nullable=False)

    nome = Column(String, nullable=False)
    cpf = Column(String(15), nullable=False, unique=True, index=True)
    telefone = Column(String, nullable=False)
    email = Column(String, nullable=False)

    perfil_investidor = Column(String, nullable=False, default="MODERADO")

    correntista = Column(Boolean, nullable=False, default=True)
    saldo_cc = Column(Float, nullable=False, default=0.0)
    cheque_especial_contratado = Column(Boolean, nullable=False, default=False)
    limite_cheque_especial = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        UniqueConstraint("agencia", "numero_conta", name="uix_agencia_numero"),
    )

    investimentos = relationship("Investimento", back_populates="conta")


class Investimento(Base):
    __tablename__ = "investimentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    agencia = Column(String(4), nullable=False)
    numero_conta = Column(String(8), nullable=False)
    tipo_investimento = Column(String, nullable=False)  # RENDA_FIXA, ACOES, FUNDOS, CRIPTO
    valor_investido = Column(Float, nullable=False)
    ticker = Column(String, nullable=True)
    rentabilidade = Column(Float, nullable=False, default=0.0)
    ativo = Column(Boolean, nullable=False, default=True)
    data_aplicacao = Column(DateTime(timezone=True), nullable=False, default=func.now(), server_default=func.now())

    conta_id = Column(UUID(as_uuid=True), ForeignKey("contas.id"))

    conta = relationship("Conta", back_populates="investimentos")

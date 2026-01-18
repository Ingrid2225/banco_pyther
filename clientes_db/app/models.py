
from sqlalchemy import Column, Integer, String, Boolean, Float, UniqueConstraint
from .db import Base

class Conta(Base):
    __tablename__ = "contas"

    id = Column(Integer, primary_key=True, index=True)

    agencia = Column(String, nullable=False)
    numero_conta = Column(String, nullable=False)

    nome = Column(String, nullable=False)
    cpf = Column(String(15), nullable=False, unique=True, index=True)
    telefone = Column(Integer, nullable=False)
    email = Column(String, nullable=False)

    correntista = Column(Boolean, nullable=False, default=True)
    saldo_cc = Column(Float, nullable=False, default=0.0)

    cheque_especial_contratado = Column(Boolean, nullable=False, default=False)
    limite_cheque_especial = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        UniqueConstraint("agencia", "numero_conta", name="uix_agencia_numero"),
    )

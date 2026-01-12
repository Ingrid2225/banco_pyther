
from sqlalchemy import Column, Integer, String, Boolean, Float, CheckConstraint
from .db import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    telefone = Column(Integer, nullable=False)
    correntista = Column(Boolean, nullable=False, default=False)
    saldo_cc = Column(Float, nullable=False, default=0.0)


    __table_args__ = (CheckConstraint("saldo_cc >= 0.0", name="saldo_nao_negativo"),)


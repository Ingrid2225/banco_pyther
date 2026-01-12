
from fastapi import FastAPI
from .db import Base, engine
from .routers import clientes

# Cria as tabelas no SQLite ao iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="JAVER - clientes_db",
    version="1.0.0",
    description="Serviço interno de armazenamento (SQLite) para clientes do banco JAVER."
)

app.include_router(clientes.router)


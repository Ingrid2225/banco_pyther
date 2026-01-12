
from fastapi import FastAPI
from .routers import clientes

app = FastAPI(
    title="JAVER - clientes_api",
    version="1.0.0",
    description="Serviço público (gateway) com CRUD e cálculo de score (saldo_cc * 0,1)."
)

app.include_router(clientes.router)


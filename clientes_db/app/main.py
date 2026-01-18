
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .db import Base, engine
from .routers import contas

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PYTHER - contas_db",
    version="1.0.0",
    description="Serviço interno de armazenamento (SQLite) para contas do banco PYTHER."
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):

    custom_messages = {
        "agencia": "Agência deve ter entre 3 e 4 dígitos.",
        "numero_conta": "Número da conta deve ter entre 4 e 8 dígitos.",
        "cpf": "CPF deve ter exatamente 11 dígitos.",
        "telefone": "Telefone deve conter entre 10 e 11 dígitos numéricos.",
        "saldo": "Saldo precisa ser maior que zero.",
        "limite": "O limite deve ser maior ou igual a zero.",
        "habilitado": "O campo habilitado deve ser True ou False."
    }

    errors = []
    for err in exc.errors():
        field = err['loc'][-1]
        msg = custom_messages.get(field, err['msg'])
        errors.append({"campo": field, "mensagem": msg})

    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "status": 422,
                "code": "VALIDACAO_REQUISICAO",
                "message": "Dados de requisição inválidos.",
                "errors": errors
            }
        }
    )

app.include_router(contas.router)

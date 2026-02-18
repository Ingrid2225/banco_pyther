from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .db import Base, engine
from .routers import contas, investimentos

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PYTHER - clientes_db",
    version="1.0.0",
    description="Serviço interno de armazenamento (SQLite) para contas e investimentos do banco PYTHER."
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):


    custom_messages = {
        "agencia": "Agência deve ter entre 3 e 4 dígitos.",
        "numero_conta": "Número da conta deve ter entre 4 e 8 dígitos.",
        "cpf": "CPF deve ter exatamente 11 dígitos.",
        "telefone": "Telefone deve conter entre 10 e 11 dígitos numéricos.",
        "limite": "O limite deve ser maior ou igual a zero.",
        "habilitado": "O campo habilitado deve ser True ou False.",
    }

    errors = []
    for err in exc.errors():
        field = err["loc"][-1]
        type_ = err.get("type")
        msg_default = err.get("msg", "")


        if field == "valor_investido" and (
            type_ == "value_error.number.not_gt"
            or "greater than 0" in msg_default.lower()
            or "not greater than" in msg_default.lower()
        ):
            msg = "Não é permitido aplicar um investimento com valor investido menor ou igual a zero."


        elif field in custom_messages:
            msg = custom_messages[field]


        else:
            msg = msg_default

        errors.append({"campo": field, "mensagem": msg})

    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "status": 422,
                "code": "VALIDACAO_REQUISICAO",
                "message": "Dados de requisição inválidos.",
                "errors": errors,
            }
        },
    )


app.include_router(contas.router)
app.include_router(investimentos.router)

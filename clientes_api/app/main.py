
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .routers import contas


app = FastAPI(
    title="PYTHER - contas_api",
    version="2.0.0",
    description="API pública (gateway) das contas. Não expõe ID. Calcula score e encaminha operações ao serviço interno clientes_db."
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):

    custom_messages = {
        "agencia": "Agência deve ter entre 3 e 4 dígitos numéricos.",
        "numero_conta": "Número da conta deve ter entre 4 e 8 dígitos numéricos.",
        "cpf": "CPF deve ter exatamente 11 números.",
        "telefone": "Telefone deve ter entre 10 e 11 dígitos numéricos.",
        "saldo": "O valor precisa ser maior que zero.",
        "limite": "O limite deve ser maior ou igual a zero.",
        "habilitado": "O campo 'habilitado' deve ser True ou False."
    }

    errors = []

    for err in exc.errors():
        loc = err.get("loc", [])
        field = loc[-1] if loc else None
        default_msg = err.get("msg")
        friendly_msg = custom_messages.get(field, default_msg)

        errors.append({
            "campo": field,
            "mensagem": friendly_msg
        })

    return JSONResponse(
        status_code=422,
        content={
            "detail": {
                "status": 422,
                "code": "VALIDACAO_REQUISICAO",
                "message": "Os dados enviados são inválidos.",
                "errors": errors
            }
        }
    )


app.include_router(contas.router)

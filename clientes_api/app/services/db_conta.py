import httpx
from fastapi import HTTPException


class DbConta:
    def __init__(self, base_url: str = "http://localhost:8002"):

        self.base_url = base_url.rstrip("/")

    async def _request(self, method: str, endpoint: str, payload: dict | None = None):
        url = f"{self.base_url}{endpoint}"

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.request(method, url, json=payload)
                r.raise_for_status()
                return r.json() if r.text else None

        except httpx.HTTPStatusError as e:

            try:
                payload = e.response.json()
                detail = payload.get("detail", {})
            except Exception:
                detail = {
                    "status": e.response.status_code,
                    "code": "ERRO_CLIENTES_DB",
                    "message": e.response.text
                }

            raise HTTPException(status_code=e.response.status_code, detail=detail)

        except httpx.RequestError:

            raise HTTPException(
                status_code=503,
                detail={
                    "status": 503,
                    "code": "CLIENTES_DB_INDISPONIVEL",
                    "message": "clientes_db indisponível"
                }
            )


    async def criar_conta(self, payload: dict) -> dict:
        return await self._request("POST", "/contas", payload)

    async def listar_contas(self) -> list[dict]:
        return await self._request("GET", "/contas")

    async def obter_conta(self, agencia: str, numero_conta: str) -> dict:
        # força string para evitar mismatch com o banco
        agencia = str(agencia)
        numero_conta = str(numero_conta)
        return await self._request("GET", f"/contas/{agencia}/{numero_conta}")

    async def atualizar_conta(self, agencia: str, numero_conta: str, payload: dict) -> dict:
        agencia = str(agencia)
        numero_conta = str(numero_conta)
        return await self._request("PUT", f"/contas/{agencia}/{numero_conta}", payload)

    async def desativar_conta(self, agencia: str, numero_conta: str) -> None:
        agencia = str(agencia)
        numero_conta = str(numero_conta)
        return await self._request("DELETE", f"/contas/{agencia}/{numero_conta}/desativar")

    async def depositar(self, payload: dict) -> dict:
        return await self._request("POST", "/contas/operacoes/depositar", payload)

    async def sacar(self, payload: dict) -> dict:
        return await self._request("POST", "/contas/operacoes/sacar", payload)

    async def cadastrar_cheque_especial(self, id_: int, payload: dict) -> dict:
        return await self._request("PUT", f"/contas/{id_}/cheque_especial/cadastrar", payload)

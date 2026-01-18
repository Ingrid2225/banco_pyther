
import httpx

class DbConta:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")

    async def criar_conta(self, payload: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base_url}/contas", json=payload, timeout=10)
            r.raise_for_status()
            return r.json()

    async def listar_contas(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/contas", timeout=10)
            r.raise_for_status()
            return r.json()

    async def obter_conta(self, agencia: str, numero_conta: str) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/contas/{agencia}/{numero_conta}", timeout=10)
            r.raise_for_status()
            return r.json()

    async def atualizar_conta(self, agencia: str, numero_conta: str, payload: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.put(
                f"{self.base_url}/contas/{agencia}/{numero_conta}",
                json=payload,
                timeout=10
            )
            r.raise_for_status()
            return r.json()

    async def desativar_conta(self, agencia: str, numero_conta: str) -> None:
        async with httpx.AsyncClient() as client:
            r = await client.delete(
                f"{self.base_url}/contas/{agencia}/{numero_conta}/desativar",
                timeout=10
            )
            r.raise_for_status()
            return None

    async def depositar(self, payload: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/contas/operacoes/depositar",
                json=payload,
                timeout=10
            )
            r.raise_for_status()
            return r.json()

    async def sacar(self, payload: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"{self.base_url}/contas/operacoes/sacar",
                json=payload,
                timeout=10
            )
            r.raise_for_status()
            return r.json()

    async def cadastrar_cheque_especial(self, id_: int, payload: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.put(
                f"{self.base_url}/contas/{id_}/cheque_especial/cadastrar",
                json=payload,
                timeout=10
            )
            r.raise_for_status()
            return r.json()

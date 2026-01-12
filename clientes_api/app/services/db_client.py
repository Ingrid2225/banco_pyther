
import httpx

class DbClient:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url.rstrip("/")

    async def create_cliente(self, payload: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{self.base_url}/clientes", json=payload, timeout=10)
            r.raise_for_status()
            return r.json()

    async def get_cliente(self, id_: int) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/clientes/{id_}", timeout=10)
            r.raise_for_status()
            return r.json()

    async def list_clientes(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            r = await client.get(f"{self.base_url}/clientes", timeout=10)
            r.raise_for_status()
            return r.json()

    async def update_cliente(self, id_: int, payload: dict) -> dict:
        async with httpx.AsyncClient() as client:
            r = await client.put(f"{self.base_url}/clientes/{id_}", json=payload, timeout=10)
            r.raise_for_status()
            return r.json()

    async def delete_cliente(self, id_: int) -> None:
        async with httpx.AsyncClient() as client:
            r = await client.delete(f"{self.base_url}/clientes/{id_}", timeout=10)
            r.raise_for_status()
            return None


import httpx
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import HTTPException


class DataClient:

    def __init__(
        self,
        clientes_db_url: str = "http://localhost:8002",
        clientes_api_url: str = "http://localhost:8001",
    ):
        self.clientes_db_url = clientes_db_url.rstrip("/")
        self.clientes_api_url = clientes_api_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=10.0)

    # ============================
    # CLIENTES_DB — CONTAS
    # ============================

    async def get_conta(self, agencia: str, numero_conta: str) -> Optional[Dict[str, Any]]:
        url = f"{self.clientes_db_url}/contas/{agencia}/{numero_conta}"
        resp = await self.client.get(url)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    async def criar_conta(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.clientes_db_url}/contas"
        resp = await self.client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def listar_contas(self) -> List[Dict[str, Any]]:
        url = f"{self.clientes_db_url}/contas"
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    async def atualizar_conta(self, agencia: str, numero_conta: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.clientes_db_url}/contas/{agencia}/{numero_conta}"
        resp = await self.client.put(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def desativar_conta(self, agencia: str, numero_conta: str):
        url = f"{self.clientes_db_url}/contas/{agencia}/{numero_conta}/desativar"
        resp = await self.client.delete(url)
        resp.raise_for_status()
        return None

    async def depositar(self, agencia: str, numero_conta: str, valor: float) -> Dict[str, Any]:
        url = f"{self.clientes_db_url}/contas/operacoes/depositar"
        payload = {"agencia": agencia, "numero_conta": numero_conta, "valor": valor}
        resp = await self.client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def sacar(self, agencia: str, numero_conta: str, valor: float) -> Dict[str, Any]:
        url = f"{self.clientes_db_url}/contas/operacoes/sacar"
        payload = {"agencia": agencia, "numero_conta": numero_conta, "valor": valor}
        resp = await self.client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    # ============================
    # CLIENTES_DB — INVESTIMENTOS
    # ============================

    async def list_investimentos_por_conta(self, agencia: str, numero_conta: str) -> List[Dict[str, Any]]:
        url = f"{self.clientes_db_url}/internal/investimentos/conta/{agencia}/{numero_conta}"
        resp = await self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    async def create_investimento(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not payload.get("agencia") or not payload.get("numero_conta"):
            raise HTTPException(
                status_code=400,
                detail={
                    "status": 400,
                    "code": "AGENCIA_CONTA_OBRIGATORIA",
                    "message": "Payload deve conter agencia e numero_conta"
                }
            )

        investimento_payload = {
            "agencia": payload["agencia"],
            "numero_conta": payload["numero_conta"],
            "tipo_investimento": payload["tipo_investimento"],
            "valor_investido": payload["valor_investido"],
            "rentabilidade": payload.get("rentabilidade", 0.0),
            "ativo": payload.get("ativo", True),
            "ticker": payload.get("ticker"),
            "data_aplicacao": (
                payload["data_aplicacao"].isoformat()
                if payload.get("data_aplicacao") and hasattr(payload["data_aplicacao"], "isoformat")
                else datetime.utcnow().isoformat()
            ),
        }

        url = f"{self.clientes_db_url}/internal/investimentos"
        resp = await self.client.post(url, json=investimento_payload)
        resp.raise_for_status()
        return resp.json()

    async def update_investimento(self, investimento_id: str, payload: dict):
        url = f"{self.clientes_db_url}/internal/investimentos/{investimento_id}"
        resp = await self.client.put(url, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def resgate_total(self, agencia: str, numero_conta: str, ticker: str):
        url = f"{self.clientes_db_url}/internal/investimentos/{agencia}/{numero_conta}/resgate_total/{ticker}"
        resp = await self.client.put(url)
        resp.raise_for_status()
        return resp.json()

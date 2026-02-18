
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .routers import investimentos
from .services.data_client import DataClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    dc = DataClient()
    yield



app = FastAPI(
    title="PYInvest Gateway ",

)


app.include_router(investimentos.router)
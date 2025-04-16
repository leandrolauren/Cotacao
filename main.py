import datetime
import logging
from zoneinfo import ZoneInfo

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.auth_routes import auth_router
from backend.api.calculation_routes import calculation_router
from backend.api.stock_routes import stock_router

sp_timezone = ZoneInfo("America/Sao_Paulo")

# Configuração de logging
logging.Formatter.converter = lambda *args: datetime.datetime.now(
    tz=sp_timezone
).timetuple()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - origin: %(name)s - message: %(message)s",
    datefmt="%d-%m-%Y %H:%M:%S",
    force=True,
)


app = FastAPI(title="API Cotacao", version="1.0.0")

app.include_router(stock_router)
app.include_router(calculation_router)
app.include_router(auth_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

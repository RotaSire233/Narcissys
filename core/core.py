from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger as log
from .network.access import start, ending

@asynccontextmanager
async def lifespan(app: FastAPI):
    await start()
    _start_compenents()
    yield
    ending()

app = FastAPI(title="Narcissys System", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
    
def _start_compenents():
    from .api_service import (model_service,
                              ladder_service,
                              file_service,
                              mqtt_service
                              )
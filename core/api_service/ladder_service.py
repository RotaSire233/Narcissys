import json
from core.core import app
from fastapi import APIRouter
from typing import Dict
from loguru import logger as _logger
from core.ladder_backend import *
import os


router = APIRouter(prefix="/api/ladder", tags=["ladder"])


@router.post("/components/ladder/run")
async def compile_ladder(key: Dict):
   pass


app.include_router(router)
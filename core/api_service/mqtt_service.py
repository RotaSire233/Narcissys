import os
from fastapi import APIRouter, HTTPException
from loguru import logger as _logger
from dataclasses import dataclass
from core.core import app
from core.network.access import regist_sensor
from loguru import logger as log

router = APIRouter(prefix="/api/mqtt", tags=["mqtt"])

@router.get("/devices")
async def get_devices():
    """获取所有已注册设备"""
    devices = regist_sensor.get_all_devices()
    return {"devices": devices}

app.include_router(router)
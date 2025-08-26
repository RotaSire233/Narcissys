import os
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from loguru import logger as _logger
from core.network.mqtt import mqtt_sub
from dataclasses import dataclass
from core.core import app
import json
from threading import Lock


@dataclass(frozen=True)
class SystemInfo:
    SYSTEM_CONFIG = {
        "endpoint": "localhost",
        "client_id": "sensor_monitor",
        "username": "",
        "password": ""
    }
    REGIST = "syst/regist"
    UNREGIST = "syst/unregist"

class MqttCache:
    def __init__(self):
        self.system_cache = {}
        self.namespace = {}
        self._lock = Lock()

    def regist_device(self, topic: str, payload: dict):
        try:
            device_id = payload.get("device_id")
            device_info = payload.get("device_info")
            if device_id and device_info:
                with self._lock:
                    self.system_cache[device_id] = device_info
                    self.namespace[device_id] = []
                    for sensor_name in device_info.get("sensors", []):
                        self.namespace[device_id].append(sensor_name)
                    
                _logger.info(f"设备 {device_id} 注册成功")
            else:
                _logger.warning(f"设备注册信息不完整: {payload}")
        except Exception as e:
            _logger.error(f"设备注册失败: {e}")

    def del_device(self, topic: str, payload: dict):
        try:
            device_id = payload.get("device_id")
            with self._lock:
                if device_id and device_id in self.system_cache:
                    self.system_cache.pop(device_id)
                    _logger.info(f"设备 {device_id} 注销成功")
                else:
                    _logger.warning(f"尝试注销不存在的设备: {device_id}")
        except Exception as e:
            _logger.error(f"设备注销失败: {e}")

    def get_all_devices(self):
        with self._lock:
            return self.system_cache.copy()

    def get_all_namespaces(self):
        with self._lock:
            return self.namespace.copy()    


sub = mqtt_sub.MqttSubscriber(SystemInfo.SYSTEM_CONFIG)
cach = MqttCache()

# 订阅注册和注销主题
try:
    sub.subscribe(SystemInfo.REGIST, cach.regist_device)
    sub.subscribe(SystemInfo.UNREGIST, cach.del_device)
except Exception as e:
    raise HTTPException(status_code=500, detail=f"设备路由订阅失败: {e}")

router = APIRouter(prefix="/api/mqtt", tags=["mqtt"])

@router.get("/devices")
async def get_devices():
    """获取所有已注册设备"""
    devices = cach.get_all_devices()
    return {"devices": devices}

app.include_router(router)



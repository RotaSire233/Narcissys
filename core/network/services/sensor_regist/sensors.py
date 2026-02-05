import json
import os
from loguru import logger as log
import asyncio
from threading import Lock

from .config import Regist
from core.network.access import regist_sensor

class RegistSensor:
    def __init__(self):
        self.registed = {}
        self.system_cache = {}
        self._lock = Lock()

    def regist_device(self, topic: str, payload: dict):
        try:
            log.info(f"[SensorRegist] 收到设备注册请求: {topic} {payload}")
            device_id = payload.get("device_id")
            device_info = payload.get("device_info")
            name_list = []
            sys_info = {}
            for item in device_info:
                sensor_name = item.get("name")
                name_list.append(sensor_name)
                sys_info[sensor_name] = item.get("type")

            if device_id and device_id not in self.registed:
                with self._lock:
                    self.registed[device_id] = name_list
                    self.system_cache[device_id] = sys_info

                log.info(f"[SensorRegist] 设备 {device_id} 注册成功")
            else:
                log.warning(f"[SensorRegist] 设备注册信息不完整: {payload}")
        except Exception as e:
            log.error(f"[SensorRegist] 设备注册失败: {e}")

    def del_device(self, topic: str, payload: dict):
        try:
            device_id = payload.get("device_id")
            with self._lock:
                if device_id and device_id in self.registed:
                    self.registed.pop(device_id)
                    log.info(f"[SensorRegist] 设备 {device_id} 注销成功")
                else:
                    log.warning(f"[SensorRegist] 尝试注销不存在的设备: {device_id}")
        except Exception as e:
            log.error(f"[SensorRegist] 设备注销失败: {e}")

    def get_all_devices(self):
        with self._lock:
            return self.registed.copy()
        
    def get_device_info(self, device_id: str):
        with self._lock:
            if device_id and device_id in self.system_cache:
                return self.system_cache[device_id]
            else:
                log.warning(f"[SensorRegist] 尝试获取不存在的设备信息: {device_id}")
                return None
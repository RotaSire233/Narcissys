import json
import os
from loguru import logger as log
import asyncio
from threading import Lock
from fastapi import HTTPException
from .net_manager import ServerManager
from .mqtt.mqtt_broker import start_mosquitto
from .services.node_service.expose_client import UdpExposeClient
from ..global_infos import CONFIG_PATH, pid, ROOT_DIR
from .services.sensor_regist.sensors import RegistSensor
from .services.sensor_regist.config import Regist
from core.network.mqtt import mqtt_sub

regist_sensor = RegistSensor() # 传感器注册表
servers = ServerManager() # 服务端管理

# 注册订阅组件
expose_client = UdpExposeClient()
reg_sub = mqtt_sub.MqttSubscriber(Regist.SYSTEM_CONFIG)

with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
    config = json.load(f)
    MOSQUITTO_PATH = config.get("mosquitto")

async def start():
    config_file = os.path.join(ROOT_DIR, 'network/mqtt/mosquitto.conf')
    broker_status, broker_pid = start_mosquitto(MOSQUITTO_PATH, config_file)
    if broker_pid is not None:
        pid.add(broker_pid)
        log.info(f"[NETWORK]MQTT代理已启动，PID: {broker_pid}")
    else:
        log.error("[NETWORK]MQTT代理启动失败")
    log.info(f"[NETWORK]网络初始化完成, Broker状态: {broker_status}")
    await asyncio.sleep(2)

    await expose_client.start_broadcasting()
    log.info("[NETWORK]UDP广播客户端已启动")

    try:
        reg_sub.subscribe(Regist.REGIST, regist_sensor.regist_device)
        reg_sub.subscribe(Regist.UNREGIST, regist_sensor.del_device)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"设备路由订阅失败: {e}")
    log.info("[NETWORK]传感器注册已启动")

async def ending():
    log.info("[NETWORK]正在关闭应用，清理资源...")
    await expose_client.stop_broadcasting()
    log.info("[NETWORK]UDP广播客户端已停止")
    pid.clear()
    log.info("[NETWORK]所有进程已终止")



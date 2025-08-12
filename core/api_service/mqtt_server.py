import os
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from loguru import logger as _logger
from core.network.mqtt.mqtt_monitor import MqttSubscriptionMonitor
from core.core import app, udp_manager


router = APIRouter(prefix="/api/mqtt", tags=["mqtt"])

# 全局MQTT订阅监控实例
subscription_monitor: MqttSubscriptionMonitor = None

def initialize_subscription_monitor():
    """初始化MQTT订阅监控器"""
    global subscription_monitor
    if subscription_monitor is None:
        # MQTT配置
        mqtt_config = {
            "endpoint": "127.0.0.1",  # 根据mosquitto.conf配置
            "client_id": "subscription_api_monitor",
        }
        
        try:
            subscription_monitor = MqttSubscriptionMonitor(mqtt_config, port=1883)
            # 启动监控
            subscription_monitor.start_monitoring()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"无法初始化MQTT订阅监控器: {str(e)}")

def shutdown_subscription_monitor():
    """关闭MQTT订阅监控器"""
    global subscription_monitor
    if subscription_monitor is not None:
        subscription_monitor = None


app.include_router(router)

def init_mqtt_subscription_monitor():
    """在应用启动时初始化MQTT订阅监控器"""
    try:
        initialize_subscription_monitor()
    except Exception as e:
        _logger.error(f"MQTT订阅监控器初始化失败: {str(e)}")

from core.core import app, udp_manager
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from network.mqtt.mqtt_monitor import MqttSubscriptionMonitor
import os

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

@router.on_event("startup")
async def startup_event():
    """应用启动时初始化MQTT订阅监控器"""
    initialize_subscription_monitor()

@router.get("/mqtt/subscriptions", summary="获取所有订阅信息")
async def get_all_subscriptions():
    """获取MQTT broker上所有主题的订阅信息"""
    global subscription_monitor
    if subscription_monitor is None:
        raise HTTPException(status_code=400, detail="MQTT订阅监控器未初始化")
    
    try:
        subscriptions = subscription_monitor.get_all_subscriptions()
        return {
            "status": "success",
            "data": subscriptions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取订阅信息失败: {str(e)}")

@router.get("/mqtt/subscriptions/{client_id}", summary="获取客户端订阅信息")
async def get_client_subscriptions(client_id: str):
    """获取特定客户端的订阅信息"""
    global subscription_monitor
    if subscription_monitor is None:
        raise HTTPException(status_code=400, detail="MQTT订阅监控器未初始化")
    
    try:
        subscriptions = subscription_monitor.get_client_subscriptions(client_id)
        return {
            "status": "success",
            "client_id": client_id,
            "subscriptions": subscriptions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户端订阅信息失败: {str(e)}")

@router.get("/mqtt/clients", summary="获取所有客户端订阅信息")
async def get_all_clients():
    """获取所有客户端及其订阅信息"""
    global subscription_monitor
    if subscription_monitor is None:
        raise HTTPException(status_code=400, detail="MQTT订阅监控器未初始化")
    
    try:
        clients = subscription_monitor.get_all_clients()
        return {
            "status": "success",
            "data": clients
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取客户端信息失败: {str(e)}")

app.include_router(router)
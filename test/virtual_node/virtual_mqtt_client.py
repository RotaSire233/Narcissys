import paho.mqtt.client as paho
from paho.mqtt.enums import CallbackAPIVersion
import asyncio
from loguru import logger as _logger
from typing import Callable, Optional
import time
import json
import uuid


class VirtualMqttClient:
    def __init__(self, mqtt_config: dict, port: int = 1883):
        """
        创建一个虚拟的MQTT客户端，仅用于连接到MQTT broker
        
        :param mqtt_config: MQTT配置字典，包含endpoint, client_id, username, password等
        :param port: MQTT Broker端口，默认为1883
        """
        self.config = mqtt_config
        self.client = paho.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=mqtt_config.get("client_id", "virtual_client"),
            reconnect_on_failure=True,
            protocol=paho.MQTTv5
        )

        if mqtt_config.get("username") and mqtt_config.get("password"):
            _logger.debug("[VIRTUAL-MQTT][INFO] 使用用户名密码进行认证")
            self.client.username_pw_set(mqtt_config["username"], mqtt_config["password"])

        try:
            self.client.connect(mqtt_config["endpoint"], port=port)
            self.client.loop_start()
            _logger.debug("[VIRTUAL-MQTT][SUCCESS] 虚拟MQTT客户端连接成功")
        except Exception as e:
            _logger.error(f"[VIRTUAL-MQTT][ERROR] 虚拟MQTT客户端连接失败: {e}")

    def publish_registration(self, device_id: str = None, device_info: dict = None):
        """
        发布设备注册消息
        
        :param device_id: 设备ID，如果未提供则自动生成
        :param device_info: 设备信息字典
        """
        if device_id is None:
            device_id = f"device_{uuid.uuid4().hex[:8]}"
            
        if device_info is None:
            _logger.warning("[VIRTUAL-MQTT][WARNING] 未提供设备信息")
            return None
            
        registration_msg = {
            "device_id": device_id,
            "device_info": device_info
        }
        
        try:
            self.client.publish("syst/regist", json.dumps(registration_msg), qos=1)
            _logger.info(f"[VIRTUAL-MQTT][REGISTER] 发布注册消息: {registration_msg}")
            return device_id
        except Exception as e:
            _logger.error(f"[VIRTUAL-MQTT][ERROR] 发布注册消息失败: {e}")
            return None

    def publish_unregistration(self, device_id: str):
        """
        发布设备注销消息
        
        :param device_id: 要注销的设备ID
        """
        unregistration_msg = {
            "device_id": device_id
        }
        
        try:
            self.client.publish("syst/unregist", json.dumps(unregistration_msg), qos=1)
            _logger.info(f"[VIRTUAL-MQTT][UNREGISTER] 发布注销消息: {unregistration_msg}")
        except Exception as e:
            _logger.error(f"[VIRTUAL-MQTT][ERROR] 发布注销消息失败: {e}")

    def publish_custom_message(self, topic: str, payload: dict, qos: int = 1):
        """
        发布自定义消息
        
        :param topic: 主题
        :param payload: 消息内容
        :param qos: 服务质量等级
        """
        try:
            self.client.publish(topic, json.dumps(payload), qos=qos)
            _logger.info(f"[VIRTUAL-MQTT][PUBLISH] 发布消息到 {topic}: {payload}")
        except Exception as e:
            _logger.error(f"[VIRTUAL-MQTT][ERROR] 发布消息失败: {e}")

    def subscribe(self, topic: str, qos: int = 1, callback: Optional[Callable] = None) -> bool:
        """
        订阅指定主题
        
        :param topic: 要订阅的主题
        :param qos: 服务质量等级
        :param callback: 消息回调函数，格式为 callback(client, userdata, message)
        :return: 订阅是否成功
        """
        try:
            if callback:
                self.client.on_message = callback
            
            result, mid = self.client.subscribe(topic, qos=qos)
            _logger.info(f"[VIRTUAL-MQTT][SUBSCRIBE] 订阅主题 {topic}")
            return result == paho.MQTT_ERR_SUCCESS
        except Exception as e:
            _logger.error(f"[VIRTUAL-MQTT][ERROR] 订阅主题失败: {e}")
            return False

    def disconnect(self):
        """
        断开与MQTT broker的连接
        """
        self.client.loop_stop()
        self.client.disconnect()
        _logger.debug("[VIRTUAL-MQTT][INFO] 虚拟MQTT客户端已断开连接")

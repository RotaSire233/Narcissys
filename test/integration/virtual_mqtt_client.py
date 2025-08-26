import paho.mqtt.client as paho
from paho.mqtt.enums import CallbackAPIVersion
from loguru import logger
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
            logger.debug("[VIRTUAL-MQTT][INFO] 使用用户名密码进行认证")
            self.client.username_pw_set(mqtt_config["username"], mqtt_config["password"])

        try:
            self.client.connect(mqtt_config["endpoint"], port=port)
            self.client.loop_start()
            logger.debug("[VIRTUAL-MQTT][SUCCESS] 虚拟MQTT客户端连接成功")
        except Exception as e:
            logger.error(f"[VIRTUAL-MQTT][ERROR] 虚拟MQTT客户端连接失败: {e}")

    def publish_registration(self, device_id: str = None, device_info: dict = None):
        """
        发布设备注册消息
        
        :param device_id: 设备ID，如果未提供则自动生成
        :param device_info: 设备信息字典
        """
        if device_id is None:
            device_id = f"device_{uuid.uuid4().hex[:8]}"
            
        if device_info is None:
            device_info = {
                "ip": "192.168.1.100",
                "sensor": [{"virtual_sensor":{}},{"virtual_sensor_1":{}}],
            }
            
        registration_msg = {
            "device_id": device_id,
            "device_info": device_info
        }
        
        try:
            self.client.publish("syst/regist", json.dumps(registration_msg), qos=1)
            logger.info(f"[VIRTUAL-MQTT][REGISTER] 发布注册消息: {registration_msg}")
            return device_id
        except Exception as e:
            logger.error(f"[VIRTUAL-MQTT][ERROR] 发布注册消息失败: {e}")
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
            logger.info(f"[VIRTUAL-MQTT][UNREGISTER] 发布注销消息: {unregistration_msg}")
        except Exception as e:
            logger.error(f"[VIRTUAL-MQTT][ERROR] 发布注销消息失败: {e}")

    def publish_custom_message(self, topic: str, payload: dict, qos: int = 1):
        """
        发布自定义消息
        
        :param topic: 主题
        :param payload: 消息内容
        :param qos: 服务质量等级
        """
        try:
            self.client.publish(topic, json.dumps(payload), qos=qos)
            logger.info(f"[VIRTUAL-MQTT][PUBLISH] 发布消息到 {topic}: {payload}")
        except Exception as e:
            logger.error(f"[VIRTUAL-MQTT][ERROR] 发布消息失败: {e}")

    def disconnect(self):
        """
        断开与MQTT broker的连接
        """
        self.client.loop_stop()
        self.client.disconnect()
        logger.debug("[VIRTUAL-MQTT][INFO] 虚拟MQTT客户端已断开连接")



def test_virtual_client():
    """
    测试虚拟客户端的注册和注销功能
    """
    # MQTT配置
    mqtt_config = {
        "endpoint": "localhost",  # 根据实际情况修改
        "client_id": "test_virtual_client"
    }
    
    # 创建并连接虚拟客户端
    virtual_client = VirtualMqttClient(mqtt_config)
    
    # 等待一段时间确保连接建立
    time.sleep(2)
    
    # 测试设备注册
    logger.info("[VIRTUAL-MQTT][TEST] 开始测试设备注册")
    device_id = virtual_client.publish_registration()
    
    """# 等待消息被处理
    logger.info(f"[VIRTUAL-MQTT][TEST] 设备 {device_id} 已注册，等待5秒后尝试注销")
    time.sleep(5)
    
    # 测试设备注销
    if device_id:
        logger.info("[VIRTUAL-MQTT][TEST] 开始测试设备注销")
        virtual_client.publish_unregistration(device_id)
        logger.info("[VIRTUAL-MQTT][TEST] 设备注销消息已发送")
    
    # 等待消息被处理
    time.sleep(2)
    
    # 测试自定义消息
    logger.info("[VIRTUAL-MQTT][TEST] 开始测试自定义消息")
    virtual_client.publish_custom_message(
        "test/topic", 
        {"message": "Hello from virtual client", "timestamp": time.time()}
    )
    
    # 等待消息被处理
    time.sleep(1)
    
    # 断开连接
    virtual_client.disconnect()
    """



if __name__ == "__main__":
    test_virtual_client()
    # 保持程序运行以便观察日志
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("[VIRTUAL-MQTT][INFO] 测试程序已退出")
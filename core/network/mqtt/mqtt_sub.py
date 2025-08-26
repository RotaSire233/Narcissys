import json
import logging
import paho.mqtt.client as paho
from paho.mqtt.enums import CallbackAPIVersion

logger = logging.getLogger(__name__)

def _on_message(client, userdata, msg):
    """
    默认的 MQTT 消息回调函数
    """
    try:
        logger.debug(f"[MQTT-SUB][RECV] 收到消息 Topic: {msg.topic}")
        payload = json.loads(msg.payload.decode("utf-8"))
        logger.debug(f"[MQTT-SUB][RECV] Payload: {payload}")

        if userdata and msg.topic in userdata:
            callback = userdata[msg.topic]
            if callback:
                callback(msg.topic, payload)

    except Exception as e:
        logger.error(f"[MQTT-SUB][ERROR] 处理 MQTT 消息失败: {e}")

class MqttSubscriber:
    def __init__(self, mqtt: dict,
                 port: int = 1883,
                 on_message= _on_message):
        self.config = mqtt
        self.topic_callbacks = {}  
        self.client = paho.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=mqtt.get("client_id", "mqtt_subscriber"),
            reconnect_on_failure=True,
            protocol=paho.MQTTv5
        )

        if mqtt.get("username") and mqtt.get("password"):
            logger.debug("[MQTT-SUB][INFO] 使用用户名密码进行认证")
            self.client.username_pw_set(mqtt["username"], mqtt["password"])

        # 设置回调函数
        self.client.on_message = on_message

        try:
            self.client.connect(mqtt["endpoint"], port=port)
            self.client.loop_start()
            logger.debug("[MQTT-SUB][SUCCESS] MQTT 订阅客户端初始化完成")
        except Exception as e:
            logger.error(f"[MQTT-SUB][ERROR] MQTT 客户端连接失败: {e}")

    def subscribe(self, topic: str, on_data_ready=None):
        self.topic_callbacks[topic] = on_data_ready
        self.client.user_data_set(self.topic_callbacks)
        self.client.subscribe(topic)
        logger.debug(f"[MQTT-SUB][INFO] 已订阅 Topic: {topic}")

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
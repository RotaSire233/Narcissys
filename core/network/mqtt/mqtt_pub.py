import json
import logging
import paho.mqtt.client as paho
from paho.mqtt.enums import CallbackAPIVersion

logger = logging.getLogger(__name__)

def _on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logger.debug("[MQTT-BLOCK][SUCESS] 成功连接到 MQTT Broker!")
    else:
        logger.debug("[MQTT-BLOCK][ERROR] 连接失败，返回码=" + str(rc))

def _on_disconnect(client, userdata, flags, rc, properties=None):
    logger.debug("[MQTT-BLOCK][SUCESS] 与 Broker 断开连接，返回码=" + str(rc))

class MqttPublisher:
    def __init__(self,
                 mqtt: dict,
                 port: 1883):
        self.mqtt = mqtt
        self.client = paho.Client(
            callback_api_version = CallbackAPIVersion.VERSION2,
            client_id=mqtt['client_id'],
            reconnect_on_failure=True,
            protocol=paho.MQTTv5)
        if mqtt.get("username") and mqtt.get("password"):
            logger.debug("[MQTT-BLOCK][INFO] 使用用户名密码进行认证")
            self.client.username_pw_set(mqtt['username'], mqtt['password'])
            
        self.client.connect(mqtt['endpoint'], port=port)
        self.client.loop_start()
        self.client.on_connect = _on_connect
        self.client.on_disconnect = _on_disconnect
        logger.debug("[MQTT-BLOCK][SUCESS] MQTT 模块 Client 初始化完成")
    
    def publish_data(self, payload: dict):
        
        message = payload.copy()
        if 'data' in message:
            payload.pop('data')
        try:
            message = json.dumps(message)
            self.client.publish(message["rout"], payload=message)
            logger.debug("[MQTT-BLOCK][SUCESS] MQTT 模块 发送数据成功")

        except Exception as e:
            logger.error("[MQTT-BLOCK][ERROR] MQTT 模块 发送数据失败: %s" % e)
        
    
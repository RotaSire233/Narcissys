import json
import paho.mqtt.client as paho
from paho.mqtt.enums import CallbackAPIVersion
from loguru import logger as _logger

class MqttSubscriptionMonitor:
    """
    MQTT订阅监控器，用于监控和获取broker上的订阅信息
    """
    def __init__(self, mqtt: dict, port: int = 1883):
        """
        初始化MQTT订阅监控客户端
        :param mqtt: MQTT配置字典，包含endpoint, client_id, username, password等
        :param port: MQTT Broker端口
        """
        self.config = mqtt
        # 存储订阅信息：{topic: [client_ids]}
        self.subscription_info = {}
        # 存储客户端信息：{client_id: [topics]}
        self.client_subscriptions = {}
        
        self.client = paho.Client(
            callback_api_version=CallbackAPIVersion.VERSION2,
            client_id=f"sub_monitor_{mqtt.get('client_id', 'mqtt_client')}",
            reconnect_on_failure=True,
            protocol=paho.MQTTv5
        )

        if mqtt.get('username') and mqtt.get('password'):
            _logger.debug("[MQTT-SUB-MONITOR][INFO] 使用用户名密码进行认证")
            self.client.username_pw_set(mqtt["username"], mqtt["password"])

        # 设置回调函数
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        try:
            self.client.connect(mqtt["endpoint"], port=port)
            _logger.debug("[MQTT-SUB-MONITOR][SUCCESS] MQTT订阅监控客户端初始化完成")
        except Exception as e:
            _logger.error(f"[MQTT-SUB-MONITOR][ERROR] MQTT客户端连接失败: {e}")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """连接回调"""
        if rc == 0:
            _logger.info("[MQTT-SUB-MONITOR][SUCCESS] 成功连接到MQTT Broker")
            # 订阅系统主题以获取订阅信息（如果broker支持）
            self.client.subscribe("$SYS/broker/subscriptions/#")
            _logger.debug("[MQTT-SUB-MONITOR][INFO] 已订阅订阅信息主题")
            
            # 订阅客户端连接/断开主题
            self.client.subscribe("$SYS/broker/clients/+")
            _logger.debug("[MQTT-SUB-MONITOR][INFO] 已订阅客户端状态主题")
        else:
            _logger.error(f"[MQTT-SUB-MONITOR][ERROR] 连接失败，返回码={rc}")

    def _on_message(self, client, userdata, msg):
        """消息回调 - 处理订阅信息"""
        try:
            _logger.debug(f"[MQTT-SUB-MONITOR][MESSAGE] 收到消息 Topic: {msg.topic}")
            
            # 处理订阅相关信息
            if msg.topic.startswith("$SYS/broker/subscriptions/"):
                self._handle_subscription_info(msg)
            elif msg.topic.startswith("$SYS/broker/clients/"):
                self._handle_client_info(msg)
                
        except Exception as e:
            _logger.error(f"[MQTT-SUB-MONITOR][ERROR] 处理MQTT消息失败: {e}")

    def _handle_subscription_info(self, msg):
        """处理订阅信息"""
        # 解析订阅主题，格式可能是 $SYS/broker/subscriptions/{client_id}/{topic}
        topic_parts = msg.topic.split('/')
        if len(topic_parts) >= 5:
            client_id = topic_parts[3]
            subscribed_topic = '/'.join(topic_parts[4:])
            
            # 更新订阅信息
            if subscribed_topic not in self.subscription_info:
                self.subscription_info[subscribed_topic] = []
            if client_id not in self.subscription_info[subscribed_topic]:
                self.subscription_info[subscribed_topic].append(client_id)
                
            # 更新客户端订阅信息
            if client_id not in self.client_subscriptions:
                self.client_subscriptions[client_id] = []
            if subscribed_topic not in self.client_subscriptions[client_id]:
                self.client_subscriptions[client_id].append(subscribed_topic)
                
            _logger.info(f"[MQTT-SUB-MONITOR][SUBSCRIPTION] 客户端 {client_id} 订阅了主题 {subscribed_topic}")

    def _handle_client_info(self, msg):
        """处理客户端信息"""
        # 解析客户端主题，格式可能是 $SYS/broker/clients/{client_id}
        topic_parts = msg.topic.split('/')
        if len(topic_parts) >= 4:
            client_id = topic_parts[3]
            status = msg.payload.decode('utf-8')
            
            # 如果客户端断开连接，清理其订阅信息
            if status == "0":  # 0表示断开连接
                self._remove_client_subscriptions(client_id)
                _logger.info(f"[MQTT-SUB-MONITOR][CLIENT] 客户端 {client_id} 已断开连接")
            elif status == "1":  # 1表示连接
                _logger.info(f"[MQTT-SUB-MONITOR][CLIENT] 客户端 {client_id} 已连接")

    def _remove_client_subscriptions(self, client_id):
        """移除客户端的订阅信息"""
        # 从客户端订阅列表中移除
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
            
        # 从主题订阅列表中移除
        topics_to_remove = []
        for topic, clients in self.subscription_info.items():
            if client_id in clients:
                clients.remove(client_id)
            if not clients:  # 如果主题没有订阅者了
                topics_to_remove.append(topic)
                
        # 清理没有订阅者的主题
        for topic in topics_to_remove:
            del self.subscription_info[topic]

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """断开连接回调"""
        _logger.info(f"[MQTT-SUB-MONITOR][DISCONNECT] 与Broker断开连接，返回码={rc}")

    def start_monitoring(self):
        """
        开始监控订阅信息
        """
        self.client.loop_start()
        _logger.info("[MQTT-SUB-MONITOR][START] 开始监控MQTT订阅信息")

    def stop_monitoring(self):
        """
        停止监控订阅信息
        """
        self.client.loop_stop()
        self.client.disconnect()
        _logger.info("[MQTT-SUB-MONITOR][STOP] 停止监控MQTT订阅信息")
        
    def get_all_subscriptions(self):
        """
        获取所有订阅信息
        :return: {topic: [client_ids]} 格式的字典
        """
        return self.subscription_info.copy()
        
    def get_client_subscriptions(self, client_id):
        """
        获取特定客户端的订阅信息
        :param client_id: 客户端ID
        :return: [topics] 该客户端订阅的主题列表
        """
        return self.client_subscriptions.get(client_id, []).copy()
        
    def get_all_clients(self):
        """
        获取所有客户端的订阅信息
        :return: {client_id: [topics]} 格式的字典
        """
        return self.client_subscriptions.copy()
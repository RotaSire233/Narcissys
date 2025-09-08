import time
import asyncio
from loguru import logger as _logger
from typing import Dict, Callable, Union
import json
from test.virtual_node.udp_driver import UdpClientDriver
from virtual_mqtt_client import VirtualMqttClient
from dataclasses import dataclass

IMGFORMAT = {
            '565': 'RGB565',
            '888': 'RGB888',
            'GS8': 'Grayscale8',
            'BIN': 'Binary1'
            }

AUDFORMAT = {
            'PCM': 'PCM',
            'MP3': 'MP3',
            'AAC': 'AAC'
            }

def six_digit_timestamp():
    """获取6位时间戳"""
    current_timestamp = int(time.time())

    six_digit_ts = current_timestamp % 1000000
    return six_digit_ts

@dataclass
class SensorRegisterStatic:
    sensor_name: str
    sensor_function: Callable
    sensor_type: str
    sample_rate: int
    timestamp: int = six_digit_timestamp()

@dataclass
class SensorRegisterStream:
    sensor_name: str
    sensor_function: Callable
    sensor_type: str
    sensor_extra: Union['StreamStr', 'Image', 'Audio']
    sample_rate: int
    timestamp: int = six_digit_timestamp()
    

@dataclass
class StreamStr:
    chunk_size: int
    timely: bool
    max_chunk: Union[int, None]
    sensor_function: Callable
    

@dataclass
class Image:
    width: int
    height: int
    format: str
    sensor_function: Callable
    chunk_size: int
    def __post_init__(self):
        if self.format not in IMGFORMAT:
            raise ValueError(f"Invalid format: {self.format}. Allowed formats are: {', '.join(IMGFORMAT)}")


@dataclass
class Audio:
    sample_rate: int
    bit_depth: int
    channels: str
    format: str
    chunk_size: int
    sensor_function: Callable
    timely: bool
    max_chunk: Union[int, None]
    def __post_init__(self):
        if self.format not in AUDFORMAT:
            raise ValueError(f"Invalid format: {self.format}. Allowed formats are: {', '.join(IMGFORMAT)}")

class VirtualNode:
    def __init__(self,
                 virtual_node_addr: list = ["192.168.1.100", 8000]):
        self.sensor_register: Dict[str, Union[SensorRegisterStatic, SensorRegisterStream]] = {}
        self.virtual_node_addr = virtual_node_addr
        self.mqtt_client = None

        self.rout = None
        self.data = None
        self.driver_id = None
        self.uid = None
        self.port = None
        self.ip = None
        self.running = True

    # 传感器注册
    def register_sensor(self, sensor: Union[SensorRegisterStatic, SensorRegisterStream]):
        """
        传感器注册
        sensor_name: 传感器名称
        sensor_function: 传感器数据获取函数
        """
        self.sensor_register[sensor.sensor_name] = sensor

    def sensor_get_handler(self, client, userdata, message):
        """
        处理订阅主题收到的消息
        """
        topic = message.topic
        payload = message.payload.decode()
        _logger.info(f"[VIRTUAL-NODE][MESSAGE] 收到消息 - 主题: {topic}, 内容: {payload}")
        
        try:
            payload_json = json.loads(payload)
            _logger.info(f"[VIRTUAL-NODE][MESSAGE] 解析后的JSON数据: {payload_json}")
            
            self.rout = payload_json.get('rout')
            self.sensor = payload_json.get('sensor')
            self.driver_id = payload_json.get('driver_id')
            self.uid = payload_json.get('uid')
            self.port = payload_json.get('port')
            self.ip = payload_json.get('ip')
            
            _logger.info(f"[VIRTUAL-NODE][DETAILS] 路由: {self.rout}, 数据: {self.sensor}, 驱动ID: {self.driver_id}, UID: {self.uid}, 端口: {self.port}, IP: {self.ip}")
            
        except json.JSONDecodeError as e:
            _logger.error(f"[VIRTUAL-NODE][ERROR] JSON解析失败: {e}")
        
        for sensor in self.sensor:
            sensor_register = self.sensor_register.get(sensor, None)
            if sensor_register is not None:
                pass

        

    def subscribe_to_topics(self, topic, callback=None, qos=1):
        """
        订阅需要的主题
        """
        if self.mqtt_client:
            success = self.mqtt_client.subscribe(topic, qos=1, callback=callback)
            if success:
                _logger.info("[VIRTUAL-NODE][SUBSCRIBE] 成功订阅控制主题")
            else:
                _logger.error("[VIRTUAL-NODE][SUBSCRIBE] 订阅控制主题失败")

    def run(self):
        """
        运行虚拟节点
        """
        try:
            asyncio.run(self.async_run())
        except KeyboardInterrupt:
            _logger.info("[VIRTUAL-NODE][INFO] 程序被用户中断")

    async def async_run(self):
        """
        异步运行虚拟节点
        """
        self.udp_client = UdpClientDriver()
        broker_addr, broker_port = self.udp_client.listen_for_broadcast()
        _logger.info(f"[VIRTUAL-UDP][INFO] 监听到UDP广播{broker_addr}:{broker_port}，开始连接MQTT服务器")
        mqtt_config = {
            "endpoint": broker_addr,  
            "client_id": "test_virtual_client"
        }
        self.mqtt_client = VirtualMqttClient(mqtt_config, port=broker_port)
        
        time.sleep(2)
        
        _logger.info("[VIRTUAL-MQTT][TEST] 开始测试设备注册")
        device_info = []
        for sensor_name, sensor_register in self.sensor_register.items():
            device_info.append({sensor_name:{}})
        device = {
            "ip": self.virtual_node_addr,
            "sensor": device_info
        }
        _logger.info(f"[VIRTUAL-MQTT][TEST] 设备信息: {device}")
        device_id = self.mqtt_client.publish_registration(device_info=device)
        sensor_topic = f"syst/get/{device_id}"
        
        self.subscribe_to_topics(sensor_topic, callback=self.sensor_get_handler)

        try:
            while self.running:
                await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            _logger.info("[VIRTUAL-MQTT][INFO] 测试程序已退出")
        finally:
            self.running = False
            if self.mqtt_client:
                self.mqtt_client.disconnect()

        
import time
import asyncio
from loguru import logger as _logger
from typing import Dict, Callable, Union, Tuple
import json
from udp_driver import UdpClientDriver, UdpTypeStatic, UdpTypeStream
from virtual_mqtt_client import VirtualMqttClient
from dataclasses import dataclass
from encoder import *



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
    sensor_type: str
    sensor_extra: Union['StreamStr', 'Image', 'Audio']
    timestamp: int = six_digit_timestamp()


    
@dataclass
class StreamStr:
    chunk_size: int
    timely: bool
    sample_rate: int = None
    uid: int = None
    

@dataclass
class Image:

    width: int
    height: int
    format: str
    chunk_size: int
    sample_rate: int
    uid: int = None
    def __post_init__(self):
        if self.format not in IMGFORMAT:
            raise ValueError(f"Invalid format: {self.format}. Allowed formats are: {', '.join(IMGFORMAT)}")


@dataclass
class Audio:
    audio_sample_rate: int
    bit_depth: int
    channels: str
    format: str
    chunk_size: int
    timely: bool
    sample_rate: int = None
    max_chunk: Union[int, None] = None
    uid: int = None
    def __post_init__(self):
        if self.format not in AUDFORMAT:
            raise ValueError(f"Invalid format: {self.format}. Allowed formats are: {', '.join(IMGFORMAT)}")

class VirtualNode:
    def __init__(self,
                 virtual_node_addr: list = ["192.168.1.100", 8000]):
        self.sensor_register: Dict[str, Union[SensorRegisterStatic, SensorRegisterStream]] = {}
        self.virtual_node_addr = virtual_node_addr
        self.mqtt_client = None
        self.udp_client = None
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
            self.uid = payload_json.get('uid') # 和sensor对应列表
            self.port = payload_json.get('port')
            self.ip = payload_json.get('ip')
            
            _logger.info(f"[VIRTUAL-NODE][DETAILS] 路由: {self.rout}, 数据: {self.sensor}, 驱动ID: {self.driver_id}, UID: {self.uid}, 端口: {self.port}, IP: {self.ip}")
            
        except json.JSONDecodeError as e:
            _logger.error(f"[VIRTUAL-NODE][ERROR] JSON解析失败: {e}")
        sensor_register: Union[SensorRegisterStatic, SensorRegisterStream]
        addr = (self.ip, self.port)
        for sensor, uid in zip(self.sensor, self.uid):
            sensor_register = self.sensor_register.get(sensor, None)
            if sensor_register is not None:
                info_byte, extra_encoder = encode_function(sensor_register, uid) # 静态数据也需要一个extra来返回每次的值提供给start_periodic_send调用
                if sensor_register.sensor_type == UdpTypeStream.STR:
                    if sensor_register.sensor_extra.timely:
                        self.udp_client.send_async(info_byte, addr)
                        timely_tasks.init_task(sensor_register.sensor_name, extra_encoder)
                    else:
                        if sensor_register.sample_rate is None:
                            file_tasks.init_task(extra_encoder, addr)
                        elif sensor_register.sample_rate is not None:
                            file_tasks.init_task(extra_encoder, addr, sample_rate=sensor_register.sample_rate)
                        else:
                            pass 
                elif sensor_register.sensor_type == UdpTypeStream.AUD:
                    if sensor_register.sensor_extra.timely:
                        self.udp_client.send_async(info_byte, addr)
                        timely_tasks.init_task(sensor_register.sensor_name, extra_encoder)
                    else:
                        if sensor_register.sample_rate is None:
                            file_tasks.init_task(extra_encoder, addr)
                        elif sensor_register.sample_rate is not None:
                            file_tasks.init_task(extra_encoder, addr, sample_rate=sensor_register.sample_rate)
                        else:
                            pass
                elif sensor_register.sensor_type == UdpTypeStream.IMG:
                    
                    self.udp_client.send_async(info_byte, addr)
                    if sensor_register.sample_rate is None:
                        file_tasks.init_task(extra_encoder, addr)
                    elif sensor_register.sample_rate is not None:
                        file_tasks.init_task(extra_encoder, addr, sample_rate=sensor_register.sample_rate)
                    else:
                        pass
                    
                else:
                    self.udp_client.start_periodic_send(sensor_register.sensor_name, 
                                                        extra_encoder, 
                                                        addr, 
                                                        sensor_register.sample_rate)
                

        

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

virtual_node = VirtualNode()

class TimelyTasks:
    def __init__(self):
        self.tasks = Dict[int, Tuple[callable, Union[StrEncoder, AudioEncoder, ImageEncoder]]]

    def call_task(self, sensor_name: str, data):
        task, encoder = self.tasks.get(sensor_name,None)
        if task is not None:
            task(data, encoder)
    
    def create_task(self, sensor_name: str):
        self.tasks[sensor_name] = 'Ready'
    
    def init_task(self, sensor_name: str, encoder: Union[StrEncoder, AudioEncoder]):
        if self.tasks.get(sensor_name, None) == 'Ready':
            self.tasks[sensor_name] = (self.stream_task, encoder)
        else:
            raise Exception('任务不存在，请先注册任务: create_task(self, sensor_name: str)')
    
    def get_all_chunks(encoder: Union[StrEncoder, AudioEncoder]):
        while True:
            chunk = encoder.get_next_chunk()
            if chunk is None:
                break
            yield chunk

    def stream_task(self,data: str,
                         encoder: Union[StrEncoder, AudioEncoder]):
        uid_bytes = int_to_bytes(encoder.uid, 'uint32')
        encoder.initialize_encoder(data)
        for chunk in self.get_all_chunks(encoder):
            chunk_bytes = uid_bytes + chunk
            if virtual_node.udp_client is not None:
                virtual_node.udp_client.send_async(chunk_bytes, (virtual_node.ip, virtual_node.port))
                # 最好循环时候加一个延时
        encoder.reset_encoder()

class FileTasks:
    def __init__(self):
        self.task = {}
    
    def init_task(self, 
                 encoder: Union[ImageEncoder],
                 addr: Tuple[str, int],
                 sample_rate: Union[int, None] = None, 
                 byte_rate: Union[int, None] = None):
        if sample_rate is not None and byte_rate is not None:
            raise Exception('不能同时指定采样率与比特率')
        elif sample_rate is None and byte_rate is not None:
            pass
        elif sample_rate is not None and byte_rate is None:
            self.send_time_rate(addr, encoder, sample_rate)
        else:
            self.send_async(addr, encoder)
    
    async def send_async(self,addr, encoder: ImageEncoder):
        cur_chunck = encoder.get_next_chunk()
        while cur_chunck is not None:
            await virtual_node.udp_client.send_async(cur_chunck, addr)
            cur_chunck = encoder.get_next_chunk()
    
    async def send_time_rate(self,addr, encoder: ImageEncoder, sample_rate: int):
        interval = 1 / sample_rate if sample_rate > 0 else 0

        while True:
            cur_chunck = encoder.get_next_chunk()
            if cur_chunck is None:
                encoder.reset_encoder()
                break
            await virtual_node.udp_client.send_async(cur_chunck, addr)

            if interval > 0:
                await asyncio.sleep(interval)

    def send_byte_rate(self, addr, encoder: ImageEncoder, byte_rate: int):
        # 暂时不需要实现，虚拟节点用比特率设定有点太没必要了
        pass
            

    
timely_tasks = TimelyTasks()
file_tasks = FileTasks()
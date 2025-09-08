from core.network.mqtt.mqtt_pub import MqttPublisher
from .ladder_compile import LadderCompile
from dataclasses import dataclass
from typing import List, Dict, Tuple
from core.core import udp_manager
from loguru import logger as _logger
import json
from core.global_cache import global_uid
from core.api_service.system_config import get_local_ip

@dataclass
class DataQuest:
    id: str
    sensor: str

@dataclass
class DataPost:
    id: str
    target: str

PUBLISH_TOPIC = "syst/get"
data_location = {}

    
def process(ladder: LadderCompile):
    global data_location
    input_list = ladder.input_device
    output_list = ladder.output_device

    input_info = compile_str(input_list)
    
    from core.api_service.mqtt_server import SystemInfo
    mqtt_config = SystemInfo.SYSTEM_CONFIG.copy()
    mqtt_config['client_id'] = 'data_compiler'
    udp_id = allocate_driver_id()
    _logger.info(f'Allocate driver id: {udp_id}' )
    driver_info = udp_manager.get_driver_info(udp_id)
    device_dict = {}
    for device, sensor in input_info.items():
        if device not in device_dict:
            device_dict[device] = []
        else:
            device_dict[device].append(sensor)
    for device, sensor in device.items():
        data_location[udp_id] = device
        uid = global_uid.get_uid(device, sensor)
        try:
            publisher = MqttPublisher(mqtt_config, 1883)
            payload = {
                'rout': PUBLISH_TOPIC + "/" + device,
                'sensor': sensor,
                "driver_id": driver_info["driver_id"], 
                "uid": uid,
                "port": driver_info["port"],
                "ip": get_local_ip(),
            }
            publisher.publish_data(payload)
            _logger.info(f"发布数据成功: {payload}")
        except Exception as e:
            _logger.error(f"发布数据失败: {e}")
    return True
def compile_str(input_list):
    input_result = {}
    
    if input_list:
        for i in input_list:
            print(i)
            key, value = split_field(i).popitem()
            if key in input_result:
                if isinstance(input_result[key], list):
                    input_result[key].append(value)
                else:
                    input_result[key] = [input_result[key], value]
            else:
                input_result[key] = value
            
    return input_result
        
def split_field(field: str) -> Dict[str, str]:
    if '/' in field:
        key, value = field.split('/', 1)
        return {key: value}
    return {}
    # all 在编译过程中处理
def allocate_driver_id():
    udp_driver_id = list(udp_manager.drivers.keys())[0] if udp_manager.drivers else None
    """
    ——————————————————————————————————————————————————————————————————————————————————————————————————————————————
    # 关键注释：当前Python版本只支持单UDP管理，可能未来会考虑多驱动管理
    # 预计处理节点：C++版本/对于这个功能有需求时，添加这个特性，
    # 还是这句话Python版本作为社区版本，这个特性属于企业级特性，一般用户不需要这么复杂的玩意
    ——————————————————————————————————————————————————————————————————————————————————————————————————————————————
    """
    return udp_driver_id
    
    








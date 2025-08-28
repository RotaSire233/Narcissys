from core.network.mqtt.mqtt_pub import MqttPublisher
from .ladder_compile import LadderCompile
from dataclasses import dataclass
from typing import List, Dict, Tuple
from core.core import udp_manager
from loguru import logger as _logger
import json

@dataclass
class DataQuest:
    id: str
    sensor: str

@dataclass
class DataPost:
    id: str
    target: str

PUBLISH_TOPIC = "command/data"

    
def process(ladder: LadderCompile):
    input_list = ladder.input_device
    output_list = ladder.output_device
    input_info, output_info = compile_str(input_list, output_list)
    
    from core.api_service.mqtt_server import SystemInfo
    mqtt_config = SystemInfo.SYSTEM_CONFIG.copy()
    mqtt_config['client_id'] = 'data_compiler'
    udp_id = allocate_driver_id()
    driver_info = udp_manager.get_driver_info(udp_id)
    for device, sensor in input_info.items():
        try:
            publisher = MqttPublisher(mqtt_config, 1883)
            payload = {
                'rout': PUBLISH_TOPIC + "/" + device,
                'data': sensor,
                "driver_id": driver_info["driver_id"],
                "port": driver_info["port"],
                "ip": driver_info["ip"],
            }
            publisher.publish_data(payload)
        except Exception as e:
            _logger.error(f"发布数据失败: {e}")
    return True
def compile_str(input_list, output_list):
    input_result = {}
    output_result = {}
    
    for i in input_list:
        key, value = split_field(i).popitem()
        if key in input_result:
            if isinstance(input_result[key], list):
                input_result[key].append(value)
            else:
                input_result[key] = [input_result[key], value]
        else:
            input_result[key] = value
            
    for o in output_list:
        key, value = split_field(o).popitem()
        if key in output_result:
          
            if isinstance(output_result[key], list):
                output_result[key].append(value)
            else:
                output_result[key] = [output_result[key], value]
        else:
            output_result[key] = value
            
    return input_result, output_result
        
def split_field(field: str) -> Dict[str, str]:
    if '/' in field:
        key, value = field.split('/', 1)
        return {key: value}
    else:
        return {field: "all"}
def allocate_driver_id():
    udp_driver_id = list(udp_manager.drivers.keys())[0] if udp_manager.drivers else None
    # 当前这里只有单个udp，未来会添加udp集群根据压力分配的算法
    return udp_driver_id[0]
    
    








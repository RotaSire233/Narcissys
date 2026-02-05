import socket
from typing import Union, TYPE_CHECKING
from loguru import logger as _logger
import json
import asyncio
from dataclasses import dataclass
import struct
import base64


   
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

def encode_function(data_structure,
                    uid: int)->bytes:
    from udp_driver import UdpTypeStatic, UdpTypeStream, RequestType
    if data_structure.sensor_type == UdpTypeStatic.INT:
        head_btye = RequestType.INT.to_bytes
        timestamp_btye = timestamp_to_bytes(data_structure.timestamp)
        uid_btye = int_to_bytes(uid, 'uint32')
        head_btyes = head_btye + timestamp_btye + uid_btye
        data = data_structure.sensor_function
        encoder = StaticEncoder(head_btyes, data, data_structure.sensor_type)
        if type(data()) == int:
            return head_btyes + int_to_bytes(data(), 'uint32'), encoder
        else:
            return None, None
    elif data_structure.sensor_type == UdpTypeStatic.STR:
        head_btye = RequestType.STR.to_bytes
        timestamp_btye = timestamp_to_bytes(data_structure.timestamp)
        uid_btye = int_to_bytes(uid, 'uint32')
        data = data_structure.sensor_function
        length = len(data)
        length_btye = int_to_bytes(length, 'uint8')
        head_btyes = head_btye + timestamp_btye + uid_btye + length_btye
        encoder = StaticEncoder(head_btyes, data, data_structure.sensor_type)
        if type(data()) == str:
            return head_btyes + str_to_bytes(data()), encoder
        else:
            return None, None

    elif data_structure.sensor_type == UdpTypeStatic.FLO:
        head_btye = RequestType.FLO.to_bytes
        timestamp_btye = timestamp_to_bytes(data_structure.timestamp)
        uid_btye = int_to_bytes(uid, 'uint32')
        data = data_structure.sensor_function
        head_btyes = head_btye + timestamp_btye + uid_btye
        encoder = StaticEncoder(head_btyes, data, data_structure.sensor_type)
        if type(data()) == float:
            return head_btyes + float_to_bytes(data(), 'float32'), encoder
        else:
            return None, None


def timestamp_to_bytes(timestamp: int) -> bytes:
    """将时间戳转换为6字节"""
    return struct.pack('>Q', timestamp)[2:]

def float_to_bytes(value: float, float_type: str = 'float32') -> bytes:
    """
    将浮点数转换为指定类型的字节序列
    
    Args:
        value: 要转换的浮点数值
        float_type: 浮点数类型，支持 'float16', 'float32', 'float64'
    """
    if float_type == 'float16':
        return struct.pack('>e', value)  # 16位浮点数（半精度）
    elif float_type == 'float32':
        return struct.pack('>f', value)  # 32位浮点数（单精度）
    elif float_type == 'float64':
        return struct.pack('>d', value)  # 64位浮点数（双精度）
    else:
        raise ValueError(f"不支持的浮点数类型: {float_type}，支持的类型包括: float16, float32, float64")

def int_to_bytes(value: int, int_type: str = 'int32') -> bytes:
    """
    将整数转换为指定类型的字节序列
    
    Args:
        value: 要转换的整数值
        int_type: 整数类型，支持 'int8', 'int16', 'int32'
    """
    if int_type == 'int8':
        return struct.pack('>b', value)
    elif int_type == 'uint8':
        return struct.pack('>B', value)
    elif int_type == 'int16':
        return struct.pack('>h', value) 
    elif int_type == 'uint16':
        return struct.pack('>H', value)
    elif int_type == 'int32':
        return struct.pack('>i', value)
    elif int_type == 'uint32':
        return struct.pack('>I', value)
    else:
        raise ValueError(f"不支持的整数类型: {int_type}，支持的类型包括: int8, uint8, int16, uint16, int32, uint32")

def str_to_bytes(value: str) -> bytes:
    """将字符串转换为字节"""
    value_len = len(value)
    len_byte = int_to_bytes(value_len, 'uint8')
    return len_byte + value.encode('utf-8')

class StaticEncoder:
    
    def __init__(self, head: bytes, data: callable, type):
        from udp_driver import UdpTypeStatic
        self.head = head
        self.data = data
        self.encode_method = None
        if type == UdpTypeStatic.INT:
            self.encode_method = int_to_bytes
        elif type == UdpTypeStatic.STR:
            self.encode_method = str_to_bytes
        elif type == UdpTypeStatic.FLO:
            self.encode_method = float_to_bytes

    def __call__(self):
        return self.head + self.encode_method(self.data())

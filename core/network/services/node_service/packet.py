import struct
from typing import Any, Union, Final
import warnings
from PIL import Image
import numpy as np
from dataclasses import dataclass
from loguru import logger as _logger


# id/timestamp/
class BaseDecoder:
    """"解码基函数"""
    id_bytes: Final[int] = 4           # 设备id字节数
    name_len_bytes: Final[int] = 1     # 名称长度字节数
    max_name_len: Final[int] = 32      # 名称最大长度（超出只会警告）
    uid_len: Final[int] = 4            # UID长度
    timestamp_bytes: Final[int] = 6    # 时间戳字节数 

    def __init__(self , bytes: bytes):
        self._ptr = 0

        self.id = self._parse_id(bytes, self.id_bytes)
        self.timestamp = self._parse_timestamp(bytes, self.timestamp_bytes)
        self.uid = None
    def _parse_id(self,
                  data: bytes,
                  length: int) -> hex:
        """ id 解析方法 """
        if len(data) < self._ptr + length:
            raise ValueError("Insufficient data for hex field")
        segment = data[self._ptr:self._ptr+length]
        self._ptr += length
        return ''.join(f'{b:02x}' for b in segment)
    def _parse_name(self,
                    data: bytes,
                    length: int) -> str:
        """ 名称解析方法 """
        if length >= self.max_name_len:
            warnings.warn(
                f"Name length {length} exceeds max allowed {self.max_name_len}",
                "In future, name will be replaced by UID map",
                UserWarning
            )
            
        if len(data) < self._ptr + length:
            raise ValueError("Insufficient data for string field")
        segment = data[self._ptr:self._ptr+length]
        self._ptr += length

        return segment.decode(encoding='utf-8')
    def _parse_timestamp(self, data: bytes, length: int) -> int:
        """ 时间戳解析方法 """
        if len(data) < self._ptr + length:
            raise ValueError("Insufficient data for timestamp")
        timestamp = struct.unpack('>Q', b'\x00\x00' + data[self._ptr:self._ptr+6])[0]
        self._ptr += 6
        return timestamp
    
    def _parse_float32(self, data: bytes, length: int=4) -> float:
        """ float32 解析方法 """
        if len(data) < self._ptr + length:
            raise ValueError("Insufficient data for float field")
        float_value = struct.unpack('>f', data[self._ptr:self._ptr+length])[0]
        self._ptr += length
        return float_value
    
    def _parse_int32(self, data: bytes, length: int=4) -> int:
        """ int32 解析方法 """
        if len(data) < self._ptr + length:
            raise ValueError("Insufficient data for float field")
        int_value = struct.unpack('>i', data[self._ptr:self._ptr+length])[0]
        self._ptr += length
        return int_value
    
    def _parse_int(self, data: bytes, length: int) -> int:
        """ 任意 int(uint8 ~ uint128) 解析方法 """
        if len(data) < self._ptr + length:
            raise ValueError("Insufficient data for int field")
        int_value = int.from_bytes(data[self._ptr:self._ptr+length], byteorder='big')
        self._ptr += length
        return int_value
    def _parse_str(self, data: bytes, length: int) -> str:
        """ 字符串解析方法 """
        if len(data) < self._ptr + length:
            raise ValueError("Insufficient data for str field")
        str_value = data[self._ptr:self._ptr + length].decode(encoding='utf-8')
        self._ptr += length
        return str_value

#id/timestamp
# 节点心跳包
class HeartBeatDecode(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        
        
#id/timestamp/uid/value
class FloatDecode(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int(byte, 4)
        self.value = self._parse_float32(byte)

#id/timestamp/uid/value
class IntDecode(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int(byte, 4)
        self.value = self._parse_int32(byte)

#id/timestamp/uid/str_length/value
class StrDecode(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int(byte, 4)
        value_len = self._parse_int(byte, 1) 
        self.value = self._parse_str(byte, value_len)


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
            raise ValueError("Insufficient data for float field")
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
    

#id/timestamp/name_length/name
# 节点发现包
class FindDecode(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        name_len = self._parse_int(byte, 1)
        self.name = self._parse_name(byte, name_len)

#id/timestamp
# 节点心跳包
class HeartBeatDecode(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        

#id/timestamp
# 节点停止包
class StopDecode(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)

#id/timestamp/name_length/sensor_name
class SensorDecode(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        name_len = self._parse_int(byte, 1)
        self.sensor_name = self._parse_name(byte, name_len)

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

#id/timestamp/uid/value
class FltInit(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int(byte, 4)
        self.stream_length = self._parse_int32(byte)

#id/timestamp/uid/str_length/value/index
class FltValue(StrDecode):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.packet_index = self._parse_int32(byte)

#id/timestamp/uid/format/width/height
class ImgInit(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int32(byte)
        self.format = self._parse_pixel_format(byte)
        self.width = self._parse_int(byte, 2)
        self.height = self._parse_int(byte, 2)
    def _parse_pixel_format(self, data: bytes) -> str:
        """解析像素格式标识 (3字节ASCII)"""

        if len(data) < self._ptr + 3:
            raise ValueError("Insufficient data for picture type format field")
        
        fmt_code = data[self._ptr:self._ptr+3].decode('ascii')
        self._ptr += 3
        
        format_map = {
            '565': 'RGB565',
            '888': 'RGB888',
            'GS8': 'Grayscale8',
            'BIN': 'Binary1'
        }
        return format_map.get(fmt_code, f'Unknown({fmt_code})')

# id/timestamp/uid/chunck_size/chunck_data/chunck_index
class ImgValue(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int32(byte)
        self.chunk_size = self._parse_int32(byte)
        self.chunk_data = self._parse_chunk(byte, self.chunk_size)
        self.chunk_index = self._parse_int32(byte)
    def complete(self):
        return len(self.chunk_data) / self.chunk_size >= 0.95
    def _parse_chunk(self, data, length = 4):
        if len(data) < self._ptr + length:
            raise ValueError("Insufficient data for picture chunck field")
        
        segment = data[self._ptr:self._ptr+length]
        self._ptr += length

        return segment


class AudInit(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int32(byte)           # 4字节设备UID
        self.format = self._parse_audio_format(byte) # 3字节格式标识
        self.sample_rate = self._parse_int32(byte)   # 4字节采样率
        self.bit_depth = self._parse_int(byte, 1)    # 1字节位深度
        self.channels = self._parse_int(byte, 1)     # 1字节通道数
        
    def _parse_audio_format(self, data: bytes) -> str:
        """解析音频格式标识 (3字节ASCII)"""
        if len(data) < self._ptr + 3:
            raise ValueError("Insufficient data for audio format field")
        
        fmt_code = data[self._ptr:self._ptr+3].decode('ascii')
        self._ptr += 3
        
        format_map = {
            'PCM': 'PCM',
            'MP3': 'MP3',
            'AAC': 'AAC'
        }
        return format_map.get(fmt_code, f'Unknown({fmt_code})')
        

class AudValue(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int32(byte)          # 4字节设备UID
        chunk_size = self._parse_int32(byte)   # 4字节数据块大小
        self.chunk_data = self._parse_chunk(byte, chunk_size)  # 原始音频数据
        self.sample_index = self._parse_int32(byte) # 4字节采样点索引
        
    def _parse_chunk(self, data: bytes, length: int) -> bytes:
        """提取原始音频二进制数据"""
        if len(data) < self._ptr + length:
            raise ValueError("Insufficient data for audio chunk")
        
        segment = data[self._ptr:self._ptr+length]
        self._ptr += length
        return segment

@dataclass
class FindResponse:
    timestamp: int
    
@dataclass
class HeartBeatResponse:
    timestamp: int

@dataclass
class SensorResponse:
    timestamp: int
    uid: int
    name: str

@dataclass
class StopResponse:
    timestamp: int

@dataclass
class FloatResponse:
    timestamp: int
    uid: int
    value: float

@dataclass
class StringResponse:
    timestamp: int
    uid: int
    chunck: int
    value: str
    
@dataclass
class AudioResponse:
    timestamp: int
    uid: int
    chunck: int
    value: bytes


class BaseEncoder:
    """编码基类 """
    timestamp_bytes: Final[int] = 6 

    def __init__(self):
        self._buffer = bytearray()
    
    def get_bytes(self) -> bytes:
        """返回编码完成的字节流"""
        return bytes(self._buffer)

    def _encode_timestamp(self, timestamp: int) -> None:
        """时间戳编码方法 (整型 -> 6字节大端序)"""
        if timestamp.bit_length() > 48:  # 6字节 = 48位
            raise ValueError("Timestamp exceeds 6-byte limit")
        
        # 高位补0确保6字节长度
        self._buffer.extend(struct.pack('>Q', timestamp)[2:8])

    def _encode_float32(self, value: float) -> None:
        """float32编码方法 (浮点数 -> 4字节IEEE754)"""
        self._buffer.extend(struct.pack('>f', value))

    def _encode_int32(self, value: int) -> None:
        """int32编码方法 (整型 -> 4字节大端序)"""
        self._buffer.extend(struct.pack('>i', value))

    def _encode_int(self, value: int, length: int) -> None:
        """通用整型编码方法 (整型 -> 定长大端序字节)"""
        if value < 0:
            raise ValueError("Negative integers not supported")
        
        if value.bit_length() > length * 8:
            raise ValueError(f"Integer exceeds {length}-byte limit")
        
        self._buffer.extend(value.to_bytes(length, 'big'))

    def _encode_str(self, value: str) -> None:
        """字符串编码方法 (字符串 -> 长度前缀 + UTF-8字节)"""
        encoded = value.encode('utf-8')
        self._encode_int(len(encoded), 1)
        self._buffer.extend(encoded)


# Find响应编码器
class FindEncoder(BaseEncoder):
    def __init__(self, device_id: str, response: FindResponse):
        super().__init__()
        self._encode_id(device_id)
        self._encode_timestamp(response.timestamp)
        
    def _encode_id(self, device_id: str) -> None:
        """ID编码方法 (十六进制字符串 -> 字节流)"""
        if len(device_id) != 8:  # 4字节对应8个十六进制字符
            raise ValueError("Invalid ID length. Expected 8 hex chars")
        
        try:
            self._buffer.extend(bytes.fromhex(device_id))
        except ValueError:
            raise ValueError("Invalid hexadecimal ID format")


# HeartBeat响应编码器
class HeartBeatEncoder(BaseEncoder):
    def __init__(self, device_id: str, response: HeartBeatResponse):
        super().__init__()
        self._encode_id(device_id)
        self._encode_timestamp(response.timestamp)
        
    def _encode_id(self, device_id: str) -> None:
        """ID编码方法 (十六进制字符串 -> 字节流)"""
        if len(device_id) != 8:  # 4字节对应8个十六进制字符
            raise ValueError("Invalid ID length. Expected 8 hex chars")
        
        try:
            self._buffer.extend(bytes.fromhex(device_id))
        except ValueError:
            raise ValueError("Invalid hexadecimal ID format")


# Sensor响应编码器
class SensorEncoder(BaseEncoder):
    def __init__(self, device_id: str, response: SensorResponse):
        super().__init__()
        self._encode_id(device_id)
        self._encode_timestamp(response.timestamp)
        self._encode_int(response.uid, 4)
        self._encode_str(response.name)
        
    def _encode_id(self, device_id: str) -> None:
        """ID编码方法 (十六进制字符串 -> 字节流)"""
        if len(device_id) != 8:  # 4字节对应8个十六进制字符
            raise ValueError("Invalid ID length. Expected 8 hex chars")
        
        try:
            self._buffer.extend(bytes.fromhex(device_id))
        except ValueError:
            raise ValueError("Invalid hexadecimal ID format")


# Stop响应编码器
class StopEncoder(BaseEncoder):
    def __init__(self, device_id: str, response: StopResponse):
        super().__init__()
        self._encode_id(device_id)
        self._encode_timestamp(response.timestamp)
        
    def _encode_id(self, device_id: str) -> None:
        """ID编码方法 (十六进制字符串 -> 字节流)"""
        if len(device_id) != 8:  # 4字节对应8个十六进制字符
            raise ValueError("Invalid ID length. Expected 8 hex chars")
        
        try:
            self._buffer.extend(bytes.fromhex(device_id))
        except ValueError:
            raise ValueError("Invalid hexadecimal ID format")


# Float响应编码器
class FloatEncoder(BaseEncoder):
    def __init__(self, device_id: str, response: FloatResponse):
        super().__init__()
        self._encode_id(device_id)
        self._encode_timestamp(response.timestamp)
        self._encode_int(response.uid, 4)
        self._encode_float32(response.value)
        
    def _encode_id(self, device_id: str) -> None:
        """ID编码方法 (十六进制字符串 -> 字节流)"""
        if len(device_id) != 8:  # 4字节对应8个十六进制字符
            raise ValueError("Invalid ID length. Expected 8 hex chars")
        
        try:
            self._buffer.extend(bytes.fromhex(device_id))
        except ValueError:
            raise ValueError("Invalid hexadecimal ID format")


# String响应编码器
class StringEncoder(BaseEncoder):
    def __init__(self, device_id: str, response: StringResponse):
        super().__init__()
        self._encode_id(device_id)
        self._encode_timestamp(response.timestamp)
        self._encode_int(response.uid, 4)
        self._encode_int32(response.chunck)
        self._encode_str(response.value)
        
    def _encode_id(self, device_id: str) -> None:
        """ID编码方法 (十六进制字符串 -> 字节流)"""
        if len(device_id) != 8:  # 4字节对应8个十六进制字符
            raise ValueError("Invalid ID length. Expected 8 hex chars")
        
        try:
            self._buffer.extend(bytes.fromhex(device_id))
        except ValueError:
            raise ValueError("Invalid hexadecimal ID format")


# Audio响应编码器
class AudioEncoder(BaseEncoder):
    def __init__(self, device_id: str, response: AudioResponse):
        super().__init__()
        self._encode_id(device_id)
        self._encode_timestamp(response.timestamp)
        self._encode_int(response.uid, 4)
        self._encode_int32(response.chunck)
        self._encode_bytes(response.value)
        
    def _encode_id(self, device_id: str) -> None:
        """ID编码方法 (十六进制字符串 -> 字节流)"""
        if len(device_id) != 8:  # 4字节对应8个十六进制字符
            raise ValueError("Invalid ID length. Expected 8 hex chars")
        
        try:
            self._buffer.extend(bytes.fromhex(device_id))
        except ValueError:
            raise ValueError("Invalid hexadecimal ID format")
            
    def _encode_bytes(self, value: bytes) -> None:
        """字节流编码方法 (字节流 -> 长度前缀 + 字节流)"""
        self._encode_int(len(value), 4)
        self._buffer.extend(value)
        


        
        
    
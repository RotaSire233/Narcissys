import struct
from typing import Any, Union, Final
import warnings
from PIL import Image
import numpy as np
from dataclasses import dataclass
from loguru import logger as _logger

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
    

#id/timestamp/id_len/id
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
        

#id/timestamp/uid/str_length/value/index/done
class FltValue(StrDecode):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.packet_index = self._parse_int32(byte)
        done = self._parse_int(byte, 1)
        if done == 1:
            self.done = True
        else:
            self.done = False

#id/timestamp/uid/format/width/height
class ImgInit(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int32(byte)
        self.format = self._parse_pixel_format(byte)
        self.width = self._parse_int(byte, 2)
        self.height = self._parse_int(byte, 2)
        self.give_size = self.calculate_image_size()
        
    def _parse_pixel_format(self, data: bytes) -> str:
        """解析像素格式标识 (3字节ASCII)"""

        if len(data) < self._ptr + 3:
            raise ValueError("Insufficient data for picture type format field")
        
        fmt_code = data[self._ptr:self._ptr+3].decode('ascii')
        self._ptr += 3
        
        format_map = IMGFORMAT
        return format_map.get(fmt_code, f'Unknown({fmt_code})')
    
    def calculate_image_size(self):
        """
        根据图像格式、宽度和高度计算图像大小（字节）
        """
        pixels = self.width * self.height
        
        if self.format == 'RGB565':
            return pixels * 2  # 每个像素2字节
        elif self.format == 'RGB888':
            return pixels * 3  # 每个像素3字节
        elif self.format == 'Grayscale8':
            return pixels * 1  # 每个像素1字节
        else:
            return None

# id/timestamp/uid/chunck_size/chunck_data/chunck_index/done
class ImgValue(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int32(byte)
        self.chunk_size = self._parse_int32(byte)
        self.chunk_data = self._parse_chunk(byte, self.chunk_size)
        self.chunk_index = self._parse_int32(byte)
        done = self._parse_int(byte, 1)
        if done == 1:
            self.done = True
        else:
            self.done = False
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
        self.stream_length = self._parse_int32(byte)
        
    def calculate_audio_size(self, duration_seconds: float) -> int:
        """根据音频参数计算指定时长音频的大小（字节）"""
        return int(duration_seconds * self.sample_rate * self.bit_depth * self.channels / 8)
        
    def get_bitrate(self) -> int:
        """计算音频比特率 (bps)"""
        return self.sample_rate * self.bit_depth * self.channels

    def _parse_audio_format(self, data: bytes) -> str:
        """解析音频格式标识 (3字节ASCII)"""
        if len(data) < self._ptr + 3:
            raise ValueError("Insufficient data for audio format field")
        
        fmt_code = data[self._ptr:self._ptr+3].decode('ascii')
        self._ptr += 3
        
        format_map = AUDFORMAT
        return format_map.get(fmt_code, f'Unknown({fmt_code})')
        

class AudValue(BaseDecoder):
    def __init__(self, byte: bytes):
        super().__init__(byte)
        self.uid = self._parse_int32(byte)                     # 4字节设备UID
        chunk_size = self._parse_int32(byte)                   # 4字节数据块大小
        self.chunk_data = self._parse_chunk(byte, chunk_size)  # 原始音频数据
        self.sample_index = self._parse_int32(byte)            # 4字节采样点索引
        done = self._parse_int(byte, 1)
        if done == 1:
            self.done = True
        else:
            self.done = False
        
    def _parse_chunk(self, data: bytes, length: int) -> bytes:
        """提取原始音频二进制数据"""
        if len(data) < self._ptr + length:
            raise ValueError("Insufficient data for audio chunk")
        
        segment = data[self._ptr:self._ptr+length]
        self._ptr += length
        return segment
import socket
from typing import Tuple, Union
from loguru import logger as _logger
import json
import asyncio
from dataclasses import dataclass
import struct
import base64
from virtual_node import (IMGFORMAT, AUDFORMAT,
                          SensorRegisterStatic, SensorRegisterStream,
                          )
from virtual_node import Image as Istruct
from virtual_node import Audio as Astruct
from virtual_node import StreamStr as Sstruct
from udp_driver import UdpTypeStatic, UdpTypeStream, RequestType


def encode_function(data_structure: Union[SensorRegisterStatic, SensorRegisterStream])->bytes:
    if data_structure.sensor_type == UdpTypeStatic.INT:
        head = RequestType.INT
        timestamp = timestamp_to_bytes(data_structure.timestamp)
    elif data_structure.sensor_type == UdpTypeStatic.STR:
        head = RequestType.STR
        timestamp = timestamp_to_bytes(data_structure.timestamp)
    elif data_structure.sensor_type == UdpTypeStatic.FLO:
        head = RequestType.FLO
        timestamp = timestamp_to_bytes(data_structure.timestamp)
    elif data_structure.sensor_type == UdpTypeStream.STR:
        if data_structure.sensor_extra.timely:
            pass
        else:
            pass
    elif data_structure.sensor_type == UdpTypeStream.IMG:
        pass
    elif data_structure.sensor_type == UdpTypeStream.AUD:
        if data_structure.sensor_extra.timely:
            pass
        else:
            pass


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


class ImageEncoder:
    def __init__(self, image_struct: Istruct):
        self.width = image_struct.width
        self.height = image_struct.height
        self.format = image_struct.format
        self.chunk_size = image_struct.chunk_size
        # 初始化编码器状态
        self._encoder_state = None

    def initialize_encoder(self, format_code: str, width: int, height: int, image_data):
        """
        初始化编码器状态，不实际编码图像数据
        """
        from PIL import Image
        import numpy as np
        
        # 保存编码参数
        self._encoder_state = {
            'format_code': format_code,
            'width': width,
            'height': height,
            'image_data': image_data,
            'current_row': 0,  # 当前处理的行
            'current_col': 0,  # 当前处理的列
        }
        
        # 预处理图像数据（如果需要）
        if isinstance(image_data, Image.Image):
            if format_code == '565':
                # 转换为RGB格式
                self._encoder_state['processed_image'] = image_data.convert('RGB')
            elif format_code == '888':
                # 转换为RGB格式
                self._encoder_state['processed_image'] = image_data.convert('RGB')
            elif format_code == 'GS8':
                # 转换为灰度图
                self._encoder_state['processed_image'] = image_data.convert('L')
            elif format_code == 'BIN':
                # 转换为二值图像
                self._encoder_state['processed_image'] = image_data.convert('1')
        else:
            self._encoder_state['processed_image'] = image_data

    def get_next_chunk(self) -> bytes:
        """
        获取下一个图像数据块，每次调用返回一个chunk的数据
        """
        if not self._encoder_state:
            raise RuntimeError("编码器未初始化，请先调用initialize_encoder方法")
            
        format_code = self._encoder_state['format_code']
        width = self._encoder_state['width']
        height = self._encoder_state['height']
        current_row = self._encoder_state['current_row']
        current_col = self._encoder_state['current_col']
        image_data = self._encoder_state['processed_image']
        
        if current_row >= height:
            # 已经处理完所有行
            return None
            
        # 计算本次要处理的行数
        chunk_size = self.chunk_size if self.chunk_size else 1024
        chunk_data = bytearray()
        
        # 根据不同格式处理
        if format_code == '565':
            # RGB565格式处理
            from PIL import Image
            import numpy as np
            
            # 如果是PIL图像，转换为numpy数组
            if isinstance(image_data, Image.Image):
                img_array = np.array(image_data)
            else:
                img_array = image_data
                
            # 确保是三维数组 (height, width, 3)
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                bytes_per_pixel = 2
                bytes_per_row = width * bytes_per_pixel
                max_rows_in_chunk = max(1, chunk_size // bytes_per_row)
                
                # 处理行
                rows_processed = 0
                while current_row < height and rows_processed < max_rows_in_chunk and len(chunk_data) < chunk_size:
                    for x in range(current_col, width):
                        if len(chunk_data) + 2 > chunk_size and len(chunk_data) > 0:
                            # 保存当前列位置以便下次继续
                            self._encoder_state['current_col'] = x
                            self._encoder_state['current_row'] = current_row
                            return bytes(chunk_data)
                        
                        r, g, b = img_array[current_row, x]
                        # 将8位转换为5/6/5位
                        r5 = (r >> 3) & 0x1F
                        g6 = (g >> 2) & 0x3F
                        b5 = (b >> 3) & 0x1F
                        # 组合成RGB565
                        rgb565 = (r5 << 11) | (g6 << 5) | b5
                        chunk_data.extend(rgb565.to_bytes(2, byteorder='big'))
                    
                    # 移动到下一行
                    current_row += 1
                    current_col = 0
                    rows_processed += 1
            else:
                # 默认数据填充
                fill_bytes = min(chunk_size, (width * height * 2) - (current_row * width * 2 + current_col * 2))
                chunk_data.extend(b'\x00\x00' * (fill_bytes // 2))
                current_row = height  # 标记为完成
                
        elif format_code == '888':
            # RGB888格式处理
            from PIL import Image
            import numpy as np
            
            # 如果是PIL图像，转换为numpy数组
            if isinstance(image_data, Image.Image):
                img_array = np.array(image_data)
            else:
                img_array = image_data
                
            bytes_per_pixel = 3
            bytes_per_row = width * bytes_per_pixel
            
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                max_rows_in_chunk = max(1, chunk_size // bytes_per_row)
                
                # 处理行
                rows_processed = 0
                while current_row < height and rows_processed < max_rows_in_chunk and len(chunk_data) < chunk_size:
                    for x in range(current_col, width):
                        if len(chunk_data) + 3 > chunk_size and len(chunk_data) > 0:
                            # 保存当前列位置以便下次继续
                            self._encoder_state['current_col'] = x
                            self._encoder_state['current_row'] = current_row
                            return bytes(chunk_data)
                        
                        r, g, b = img_array[current_row, x]
                        chunk_data.extend(bytes([r, g, b]))
                    
                    # 移动到下一行
                    current_row += 1
                    current_col = 0
                    rows_processed += 1
            else:
                # 默认数据填充
                fill_bytes = min(chunk_size, (width * height * 3) - (current_row * width * 3 + current_col * 3))
                chunk_data.extend(b'\x00' * fill_bytes)
                current_row = height  # 标记为完成
                
        elif format_code == 'GS8':
            # 灰度图格式处理
            from PIL import Image
            import numpy as np
            
            # 如果是PIL图像，转换为numpy数组
            if isinstance(image_data, Image.Image):
                img_array = np.array(image_data)
            else:
                img_array = image_data
                
            bytes_per_pixel = 1
            bytes_per_row = width * bytes_per_pixel
            max_rows_in_chunk = max(1, chunk_size // bytes_per_row)
            
            if len(img_array.shape) == 2:
                # 已经是灰度图
                rows_processed = 0
                while current_row < height and rows_processed < max_rows_in_chunk and len(chunk_data) < chunk_size:
                    for x in range(current_col, width):
                        if len(chunk_data) + 1 > chunk_size and len(chunk_data) > 0:
                            # 保存当前列位置以便下次继续
                            self._encoder_state['current_col'] = x
                            self._encoder_state['current_row'] = current_row
                            return bytes(chunk_data)
                        
                        chunk_data.extend(bytes([img_array[current_row, x]]))
                    
                    # 移动到下一行
                    current_row += 1
                    current_col = 0
                    rows_processed += 1
            else:
                # 默认数据填充
                fill_bytes = min(chunk_size, (width * height) - (current_row * width + current_col))
                chunk_data.extend(b'\x80' * fill_bytes)
                current_row = height  # 标记为完成
                
        elif format_code == 'BIN':
            # 二值图像格式处理
            from PIL import Image
            import numpy as np
            
            # 如果是PIL图像，转换为numpy数组
            if isinstance(image_data, Image.Image):
                img_array = np.array(image_data)
            else:
                img_array = image_data
                
            bytes_per_pixel = 1
            bytes_per_row = width * bytes_per_pixel
            max_rows_in_chunk = max(1, chunk_size // bytes_per_row)
            
            if len(img_array.shape) == 2:
                # 已经是二值图像或灰度图
                rows_processed = 0
                while current_row < height and rows_processed < max_rows_in_chunk and len(chunk_data) < chunk_size:
                    for x in range(current_col, width):
                        if len(chunk_data) + 1 > chunk_size and len(chunk_data) > 0:
                            # 保存当前列位置以便下次继续
                            self._encoder_state['current_col'] = x
                            self._encoder_state['current_row'] = current_row
                            return bytes(chunk_data)
                        
                        pixel_value = 0xFF if img_array[current_row, x] > 127 else 0x00
                        chunk_data.extend(bytes([pixel_value]))
                    
                    # 移动到下一行
                    current_row += 1
                    current_col = 0
                    rows_processed += 1
            else:
                # 默认数据填充
                fill_bytes = min(chunk_size, (width * height) - (current_row * width + current_col))
                chunk_data.extend(b'\xFF' * fill_bytes)
                current_row = height  # 标记为完成
        
        # 更新状态
        self._encoder_state['current_row'] = current_row
        self._encoder_state['current_col'] = current_col
        
        return bytes(chunk_data) if chunk_data else None

    def reset_encoder(self):
        """
        重置编码器状态
        """
        if self._encoder_state:
            self._encoder_state['current_row'] = 0
            self._encoder_state['current_col'] = 0

class StrEncoder:
    def __init__(self, str_struct: Sstruct):
        self.chunk_size = str_struct.chunk_size  # 缓冲区大小
        self.timely = str_struct.timely    # False为实时模式，True为填充模式
        self._encoder_state = None

    def initialize_encoder(self, text_data: str):
        """
        初始化编码器状态
        """
        self._encoder_state = {
            'text_data': text_data,
            'current_position': 0,
            'total_length': len(text_data),
            'buffer': ""  # 缓冲区用于填充模式
        }

    def get_next_chunk(self) -> bytes:
        """
        获取下一个文本数据块
        
        Returns:
            bytes: 编码后的字节数据，如果无数据则返回None
        """
        if not self._encoder_state:
            raise RuntimeError("编码器未初始化，请先调用initialize_encoder方法")
            
        # 实时模式 (timely  = False)
        if self.timely  is False:
            current_pos = self._encoder_state['current_position']
            total_len = self._encoder_state['total_length']
            text_data = self._encoder_state['text_data']
            
            # 检查是否还有数据未处理
            if current_pos >= total_len:
                return None
                
            # 每次读取chunk_size大小的数据，即使小于chunk_size也要返回
            end_pos = min(current_pos + self.chunk_size, total_len)
            text_chunk = text_data[current_pos:end_pos]
            self._encoder_state['current_position'] = end_pos
            return text_chunk.encode('utf-8') if text_chunk else None
            
        # 填充模式 (max_chunk = True)
        else:
            # 将数据添加到缓冲区直到达到chunk_size大小
            current_pos = self._encoder_state['current_position']
            total_len = self._encoder_state['total_length']
            text_data = self._encoder_state['text_data']
            
            # 如果还有原始数据未处理，继续添加到缓冲区
            if current_pos < total_len:
                # 尝试填满缓冲区
                needed_chars = self.chunk_size - len(self._encoder_state['buffer'])
                end_pos = min(current_pos + needed_chars, total_len)
                additional_text = text_data[current_pos:end_pos]
                self._encoder_state['buffer'] += additional_text
                self._encoder_state['current_position'] = end_pos
                
            # 如果缓冲区满了或者没有更多数据了，返回缓冲区内容
            if len(self._encoder_state['buffer']) >= self.chunk_size or \
               (len(self._encoder_state['buffer']) > 0 and current_pos >= total_len):
                text_chunk = self._encoder_state['buffer']
                self._encoder_state['buffer'] = ""
                return text_chunk.encode('utf-8') if text_chunk else None
            else:
                # 缓冲区未满且还有数据要处理
                return None

    def reset_encoder(self):
        """
        重置编码器状态
        """
        if self._encoder_state:
            self._encoder_state['current_position'] = 0
            self._encoder_state['buffer'] = ""

class AudioEncoder:
    def __init__(self, audio_struct: Astruct):
        self.sample_rate = audio_struct.sample_rate
        self.bit_depth = audio_struct.bit_depth
        self.channels = audio_struct.channels
        self.format = audio_struct.format
        self.chunk_size = audio_struct.chunk_size
        self.timely = audio_struct.timely    # False为实时模式，True为填充模式
        self._encoder_state = None

    def initialize_encoder(self, audio_data: bytes):
        """
        初始化编码器状态
        
        Args:
            audio_data: 音频字节数据
        """
        self._encoder_state = {
            'audio_data': audio_data,
            'current_position': 0,
            'total_length': len(audio_data),
            'buffer': b""  # 缓冲区用于填充模式
        }

    def get_next_chunk(self) -> bytes:
        """
        获取下一个音频数据块
        
        Returns:
            bytes: 音频字节数据，如果无数据则返回None
        """
        if not self._encoder_state:
            raise RuntimeError("编码器未初始化，请先调用initialize_encoder方法")
            
        # 实时模式 (max_chunk = False)
        if self.timely is False:
            current_pos = self._encoder_state['current_position']
            total_len = self._encoder_state['total_length']
            audio_data = self._encoder_state['audio_data']
            
            # 检查是否还有数据未处理
            if current_pos >= total_len:
                return None
                
            # 每次读取chunk_size大小的数据，即使小于chunk_size也要返回
            end_pos = min(current_pos + self.chunk_size, total_len)
            audio_chunk = audio_data[current_pos:end_pos]
            self._encoder_state['current_position'] = end_pos
            return audio_chunk if audio_chunk else None
            
        # 填充模式 (timely = True)
        else:
            # 将数据添加到缓冲区直到达到chunk_size大小
            current_pos = self._encoder_state['current_position']
            total_len = self._encoder_state['total_length']
            audio_data = self._encoder_state['audio_data']
            
            # 如果还有原始数据未处理，继续添加到缓冲区
            if current_pos < total_len:
                # 尝试填满缓冲区
                needed_bytes = self.chunk_size - len(self._encoder_state['buffer'])
                end_pos = min(current_pos + needed_bytes, total_len)
                additional_audio = audio_data[current_pos:end_pos]
                self._encoder_state['buffer'] += additional_audio
                self._encoder_state['current_position'] = end_pos
                
            # 如果缓冲区满了或者没有更多数据了，返回缓冲区内容
            if len(self._encoder_state['buffer']) >= self.chunk_size or \
               (len(self._encoder_state['buffer']) > 0 and current_pos >= total_len):
                audio_chunk = self._encoder_state['buffer']
                self._encoder_state['buffer'] = b""
                return audio_chunk if audio_chunk else None
            else:
                # 缓冲区未满且还有数据要处理
                return None

    def reset_encoder(self):
        """
        重置编码器状态
        """
        if self._encoder_state:
            self._encoder_state['current_position'] = 0
            self._encoder_state['buffer'] = b""
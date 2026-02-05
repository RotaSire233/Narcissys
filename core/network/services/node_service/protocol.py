from typing import Dict, Final, ClassVar
from dataclasses import dataclass
from enum import Enum
from loguru import logger as _logger
from .packet import *


@dataclass(frozen=True)
class ProtocolField:
    """协议字段描述方式"""
    offset: int     # 字段偏移量
    length: int     # 字段长度
    def end(self) -> int:
        return self.offset + self.length
    

@dataclass(frozen=True)
class BaseProtocolHeader:
    """ 协议头解包基函数 """
    _field_map: ClassVar[Dict[str, ProtocolField]] = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._field_map = {}
        offset = 0
        for name, value in vars(cls).items():
            if isinstance(value, ProtocolField):
                object.__setattr__(value, 'offset', offset)
                cls._field_map[name] = value
                offset += value.length

@dataclass(frozen=True)
class DefaultProtocolHeaderStruct:
    """ 协议头字段的值容器 """
    channel: int
    port: int
    decode: int
    length: int


class DefaultProtocolHeader(BaseProtocolHeader):
    """" 默认协议头字段 """
    channel: ProtocolField = ProtocolField(offset=1, length=1)
    port: ProtocolField = ProtocolField(offset=1, length=1)
    decode: ProtocolField = ProtocolField(offset=1, length=1)
    length: ProtocolField = ProtocolField(offset=1, length=1)
    
    @classmethod
    def __len__(cls) -> int:
        return sum(field.length for field in cls._field_map.values())
    
    def decode_method(cls, data: bytes) -> DefaultProtocolHeaderStruct:
        field_values = {}
        for name, field in cls._field_map.items():
            value_bytes = data[field.offset:field.end()]
            value = int.from_bytes(value_bytes, byteorder='big')
            field_values[name] = value

        return DefaultProtocolHeaderStruct(**field_values)

class _RequestStruct:
    """ 请求类型和结构配置 """
    def __init__(self, channel: int, port: int, decode: int):
        self.channel = channel
        self.port = port
        self.decode = decode


class RequestType(Enum):

    HEA = 'hea', _RequestStruct(channel=0x00, port=0x00, decode=0x01)   # 心跳包
    FLO = 'flo', _RequestStruct(channel=0x01, port=0x00, decode=0x10)   # 浮点数
    INT = 'int', _RequestStruct(channel=0x01, port=0x00, decode=0x11)   # 整数
    STR = 'str', _RequestStruct(channel=0x01, port=0x00, decode=0x12)   # 字符串
    

    def __init__(self, value, struct: _RequestStruct):
        self._value_ = value
        self.struct = struct

    @classmethod
    def get_type(cls, request_type: 'RequestType') -> _RequestStruct:
        if not isinstance(request_type, RequestType):
            _logger.error(f"Invalid request type: {request_type}")
            raise ValueError(f"Invalid request type: {request_type}")
        return request_type.struct
    @classmethod
    def get_decoder(cls, channel: int, port: int, decode: int) -> callable:
        """根据channel, port, decode的值匹配返回对应的解码方法"""
        
        matched_type = None
        for response_type in cls.__members__.values():
            if (response_type.struct.channel == channel and 
                response_type.struct.port == port and 
                response_type.struct.decode == decode):
                matched_type = response_type
                break
        
        if matched_type is None:
            _logger.warning(f"No matching ResponseType found for channel={channel:#04x}, port={port:#04x}, decode={decode:#04x}")
            return cls._decode_default
        
        # 获取对应解码函数
        decoder_map = {
            cls.FLO: cls._decode_flo, 
            cls.INT: cls._decode_int,
            cls.STR: cls._decode_str
        }
        
        return decoder_map.get(matched_type, cls._decode_default)

    @classmethod
    def get_all_types(cls) -> list['RequestType']:
        return list(cls.__members__.values())
    
    @staticmethod
    def _decode_hea(data: bytes) -> HeartBeatDecode:
        """HEA包解码"""
        heart = HeartBeatDecode(data)
        id = heart.id
        timestamp = heart.timestamp

        return {'id': id, 
                'uid': None,
                'name': None,
                'timestamp': timestamp,
                }

    
    @staticmethod
    def _decode_flo(data: bytes) -> FloatDecode:
        """FLO包解码示例"""
        float_value = FloatDecode(data)
        id = float_value.id
        uid = float_value.uid
        timestamp = float_value.timestamp
        value = float_value.value
        return {
            'id': id,
            'uid': uid,
            'name': None,
            'timestamp': timestamp,
            'data': value,
            }
    
    @staticmethod
    def _decode_int(data: bytes) -> IntDecode:
        """INT包解码"""
        int_value = IntDecode(data)
        id = int_value.id
        uid = int_value.uid
        timestamp = int_value.timestamp
        value = int_value.value

        return {
            'id': id,
            'uid': uid,
            'name': None,
            'timestamp': timestamp,
            'data': value,
            }
    
    @staticmethod
    def _decode_str(data: bytes) -> StrDecode:
        """STR包解码"""
        str_value = StrDecode(data)
        id = str_value.id
        uid = str_value.uid
        timestamp = str_value.timestamp
        value = str_value.value

        return {
                'id': id,
                'uid': uid,
                'name': None,
                'timestamp': timestamp,
                'data': value,
                }
    
    @staticmethod
    def _decode_default(data: bytes) -> None:
        """默认解码"""
        return None

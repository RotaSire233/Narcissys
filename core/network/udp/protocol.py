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
    FIN = 'fin', _RequestStruct(channel=0x00, port=0x00, decode=0x00)   # 搜索包
    HEA = 'hea', _RequestStruct(channel=0x00, port=0x00, decode=0x01)   # 心跳包
    STO = 'sto', _RequestStruct(channel=0x00, port=0x00, decode=0x02)   # 停止包
    FLO = 'flo', _RequestStruct(channel=0x01, port=0x00, decode=0x10)   # 浮点数
    INT = 'int', _RequestStruct(channel=0x01, port=0x00, decode=0x11)   # 整数
    STR = 'str', _RequestStruct(channel=0x01, port=0x00, decode=0x12)   # 字符串
    FLT_I = 'flt_i', _RequestStruct(channel=0x01, port=0x00, decode=0x13)   # 流式文本初始化
    AUD_I = 'aud_i', _RequestStruct(channel=0x01, port=0x00, decode=0x14)   # 音频初始化
    IMG_I = 'img_i', _RequestStruct(channel=0x01, port=0x00, decode=0x15)   # 图片初始化
    FLT = 'flt', _RequestStruct(channel=0x01, port=0x01, decode=0x13)   # 流式文本
    AUD = 'aud', _RequestStruct(channel=0x01, port=0x01, decode=0x14)   # 音频
    IMG = 'img', _RequestStruct(channel=0x01, port=0x01, decode=0x15)   # 图片
    

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
            cls.FIN: (cls._decode_fin, "static"),
            cls.HEA: (cls._decode_hea, "static"),
            cls.STO: (cls._decode_sto, "static"),
            cls.FLO: (cls._decode_flo, "static"),
            cls.INT: (cls._decode_int, "static"),
            cls.STR: (cls._decode_str, "static"),
            cls.FLT_I: (cls._decode_flt_init, "init"),
            cls.AUD_I: (cls._decode_aud_init, "init"),
            cls.IMG_I: (cls._decode_img_init, "init"),
            cls.FLT: (cls._decode_flt, "stream"),
            cls.AUD: (cls._decode_aud, "stream"),
            cls.IMG: (cls._decode_img, "stream"),
        }
        
        return decoder_map.get(matched_type, cls._decode_default)

    @classmethod
    def get_all_types(cls) -> list['RequestType']:
        return list(cls.__members__.values())
    
    @staticmethod
    def _decode_fin(data: bytes) -> FindDecode:
        """FIN包解码"""
        find = FindDecode(data)
        id = find.id
        name = find.name
        uid = find.uid
        timestamp = find.timestamp

        return {'id': id, 
                'name': name, 
                'uid': uid, 
                'timestamp': timestamp}
    
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
    def _decode_sto(data: bytes) -> StopDecode:
        """STO包解码示例"""
        stop = StopDecode(data)
        id = stop.id
        timestamp = stop.timestamp
        return {
                'id': id, 
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
    def _decode_flt_init(data: bytes) -> FltInit:
        """FLT包流式任务解码"""
        flt_init = FltInit(data)
        id = flt_init.id
        uid = flt_init.uid
        timestamp = flt_init.timestamp
        return {
                'id': id,
                'uid': uid,
                'name': None,
                'timestamp': timestamp,
                'type': "flt"
                }
    
    @staticmethod
    def _decode_flt(data: bytes) -> FltValue:
        """FLT包解码"""
        flt_value = FltValue(data)
        id = flt_value.id
        uid = flt_value.uid
        timestamp = flt_value.timestamp
        value = flt_value.value
        chunk = flt_value.packet_index
        done = flt_value.done
        return {
                'id': id,
                'uid': uid,
                'name': None,
                'timestamp': timestamp,
                'data': value,
                'chunk': chunk,
                'done': done
                }
    
    @staticmethod
    def _decode_aud_init(data: bytes) -> dict:
        """AUD包流式任务解码"""
        aud_init = AudInit(data)
        id = aud_init.id
        uid = aud_init.uid
        timestamp = aud_init.timestamp
        formats = aud_init.format
        sample_rate = aud_init.sample_rate
        bit_depth = aud_init.bit_depth
        channels = aud_init.channels
        stream_len = aud_init.stream_length
        return {
                'id': id,
                'uid': uid,
                'name': None,
                'timestamp': timestamp,
                'format': formats,
                'sample_rate': sample_rate,
                'bit_depth': bit_depth,
                'channels': channels,
                'stream_len': stream_len,
                'type': "aud"
                }
    
    @staticmethod
    def _decode_aud(data: bytes) -> dict:
        """AUD包解码"""
        aud_value = AudValue(data)
        id = aud_value.id
        uid = aud_value.uid
        timestamp = aud_value.timestamp
        value = aud_value.chunk_data
        chunk = aud_value.sample_index
        done = aud_value.done
        return {
                'id': id,
                'uid': uid,
                'name': None,
                'timestamp': timestamp,
                'data': value,
                'chunk': chunk,
                'done': done
                }
    
    @staticmethod
    def _decode_img_init(data: bytes) -> ImgInit:
        """IMG包流式任务解码"""
        img_init = ImgInit(data)
        id = img_init.id
        uid = img_init.uid
        timestamp = img_init.timestamp
        formats = img_init.format
        size = (img_init.width, img_init.height)
        return {
                'id': id,
                'uid': uid,
                'name': None,
                'timestamp': timestamp,
                'format': formats,
                'size': size,
                'type': "img"

        }
    
    @staticmethod
    def _decode_img(data: bytes) -> ImgValue:
        """IMG包解码"""
        img_value = ImgValue(data)
        id = img_value.id
        uid = img_value.uid
        timestamp = img_value.timestamp
        complete = img_value.complete()
        data = img_value.chunk_data
        chunk = img_value.chunk_index
        done = img_value.done
        return {
                'id': id,
                'uid': uid,
                'timestamp': timestamp,
                'complete': complete,
                'data': data,
                'chunk': chunk,
                'done': done
                }
    
    @staticmethod
    def _decode_default(data: bytes) -> None:
        """默认解码"""
        return None

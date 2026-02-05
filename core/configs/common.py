from typing import Dict, Final, ClassVar
from dataclasses import dataclass
from enum import Enum
from loguru import logger as _logger

class DtypeList:
    int_8 = "int_8"
    int_16 = "int_16"
    int_32 = "int_32"

    float_16 = "float_16"
    float_32 = "float_32"
    float_64 = "float_64"

    string = "str"
    string_flow = "str_flow"

    image = "img"
    audio = "aud"

class GlobalCacheConfig:
    """ 全局缓存 配置类 """                
    CACHE_LEN_SIZE: Final[int] = 32                # 默认全局缓存长度
    CACHE_RAM_SIZE: Final[int] = 64 * 1024 * 1024  # 默认全局缓存大小
    OVERFLOW_THRESHOLD: Final[int] = 1.5              # 缓存溢出阈值
    WARNING_THRESHOLD: Final[int] = 1.2               # 缓存警告阈值


    

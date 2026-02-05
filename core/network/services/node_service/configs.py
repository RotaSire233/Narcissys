from typing import Dict, Final, ClassVar
from dataclasses import dataclass
from enum import Enum
from loguru import logger as _logger


class NodeConfigs:
    """ 设备发现/心跳包 配置类 """
    LISTEN_IP: Final[str] = '0.0.0.0'                       
    BUFFER_SIZE: Final[int] = 80 * 1024 * 1024 
    MAX_WORKERS: Final[int] = 10 

    DEFAULT_CLEAN_INTERVAL: Final[int] = 5  
    DEFAULT_NODE_TIMEOUT: Final[int] = 30 
    

    def __setattr__(self, name, value):
        """ 防止实例属性被修改 """
        raise AttributeError("NodeConfigs instances are read-only")

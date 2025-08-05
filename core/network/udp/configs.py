from typing import Dict, Final, ClassVar
from dataclasses import dataclass
from enum import Enum
from loguru import logger as _logger

__all__ = ['UdpConfigs']
# 配置日志记录


class UdpConfigs:
    """ UDP 配置类 """
    LISTEN_IP: Final[str] = '0.0.0.0'                     # 监听广播
    LISTEN_PORT_RANGE: Final[tuple[int, int]] = (1025, 2048) # UDP端口范围
    BUFFER_SIZE: Final[int] = 1024                        # socket缓冲区大小
    MAX_WORKERS: Final[int] = 10                          # 并行数据处理线程上限
    QUEUE_SIZE: Final[int] = 100                          # 数据队列大小

    DEFAULT_STATIC_CACHE_LEN_SIZE: Final[int] = 50                # 默认静态缓存长度
    DEFAULT_STATIC_CACHE_RAM_SIZE: Final[int] = 4 * 1024 * 1024   # 默认静态缓存大小
    DEFAULT_STREAM_CACHE_LEN_SIZE: Final[int] = 8                 # 默认流缓存长度
    DEFAULT_STREAM_CACHE_RAM_SIZE: Final[int] = 16 * 1024 * 1024  # 默认流缓存大小

    DEFAULT_CLEAN_INTERVAL: Final[int] = 5      # 默认清理间隔
    DEFAULT_NODE_TIMEOUT: Final[int] = 30       # 默认节点超时时间
    


    def __setattr__(self, name, value):
        """ 防止实例属性被修改 """
        raise AttributeError("UdpConfigs instances are read-only")

    @classmethod
    def validate_port(cls, port: int) -> bool:
        """验证端口是否在有效范围内"""
        return cls.LISTEN_PORT_RANGE[0] <= port <= cls.LISTEN_PORT_RANGE[1]






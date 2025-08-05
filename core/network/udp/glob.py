import threading
from typing import Optional, Set, Dict, Tuple, List
import heapq
from loguru import logger as _logger


import threading
from typing import Optional, Set


class GlobalCache:
    _instance_lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        attr_name = f"_{cls.__name__}_instance"
        if not hasattr(cls, attr_name):
            with cls._instance_lock:
                if not hasattr(cls, attr_name):
                    setattr(cls, attr_name, super(GlobalCache, cls).__new__(cls))
        return getattr(cls, attr_name)

    def __init__(self):
        if not self._initialized:
            self._init_data()
            self._initialized = True

    def _init_data(self):
        """子类实现自己的初始化逻辑"""
        raise NotImplementedError()

    def reset(self):
        """子类可重写此方法以支持测试重置"""
        self._init_data()

class PortPool(GlobalCache):
    def _init_data(self):
        """初始化端口池数据结构"""
        self._allocated_ports: Set[int] = set()
        self._port_pools: Dict[str, dict] = {}

    def register_range(self, start: int, end: int):
        """注册一个端口范围"""
        
        range_key = f"{start}-{end}"
        if range_key in self._port_pools:
            return
        self._port_pools[range_key] = {
            "start": start,
            "end": end,
            "current": start,
            "freed": []
        }

    def allocate_port(self) -> Optional[int]:
        """从任意范围中分配一个可用端口"""
        with self._instance_lock:
            for range_key, pool in self._port_pools.items():
                start = pool["start"]
                end = pool["end"]
                current = pool["current"]
                freed = pool["freed"]

                # 优先从 freed 中取
                if freed:
                    port = freed.pop(0)
                    if start <= port <= end and port not in self._allocated_ports:
                        self._allocated_ports.add(port)
                        _logger.info(f"获取端口成功: {port}")
                        return port

                # 从 current 向后找
                while current <= end:
                    if current not in self._allocated_ports:
                        self._allocated_ports.add(current)
                        pool["current"] = current + 1
                        _logger.info(f"获取端口成功: {current}")
                        return current
                    current += 1

                pool["current"] = end + 1
                _logger.info("端口已满")
            return None  # 所有范围都满

    def release_port(self, port: int):
        """释放一个端口"""
        if port not in self._allocated_ports:
            _logger.warning("释放一个未分配的端口")
            return

        with self._instance_lock:
            self._allocated_ports.discard(port)
            _logger.info(f"释放端口 {port}")

            for range_key, pool in self._port_pools.items():
                start = pool["start"]
                end = pool["end"]
                if start <= port <= end:
                    pool["freed"].append(port)
                    pool["freed"].sort()
                    break

    def has_port(self, port: int) -> bool:
        """查询端口是否已被分配"""
        return port in self._allocated_ports

    def reset(self):
        """重置状态，用于测试"""
        with self._instance_lock:
            self._init_data()
        _logger.debug(f"重置端口池")

class UidGenerator(GlobalCache):
    def _init_data(self):
        """初始化 UID 生成器的数据结构"""
        self._uid_counter = 0 
        self._uid_map: Dict[Tuple[int, str], int] = {}  # (id, name) -> uid 的映射表

    def get_uid(self, id: int, name: str) -> int:
        """获取与 (id, name) 对应的唯一 UID"""
        key = (id, name)
        if key in self._uid_map:
            return self._uid_map[key]
        
        self._uid_counter += 1
        uid = self._uid_counter
        self._uid_map[key] = uid
        _logger.info(f"UID: {uid} 输出成功")
        return uid

    def reset(self):
        """重置 UID 生成器，用于测试或重新初始化"""
        with self._instance_lock:
            self._init_data()
        _logger.info("UID 重置成功")
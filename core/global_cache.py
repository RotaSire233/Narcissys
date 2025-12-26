from .configs.configs import GlobalCacheConfig
import threading
from enum import Enum
import logging
from cachetools import LRUCache
from typing import Tuple, Union, Any, Optional, ClassVar, Dict
from dataclasses import dataclass, field
from core.network.mqtt.mqtt_pub import MqttPublisher
from loguru import logger as _logger
from collections import OrderedDict
import os


class UidGenerator:
    def __init__(self):
        """初始化 UID 生成器的数据结构"""
        self._uid_counter = 0 
        self._uid_map: Dict[Tuple[int, str], int] = {}  # (id, name) -> uid 的映射表

    def get_uid(self, id: int, sensor: str) -> int:
        """获取与 (id, name) 对应的唯一 UID"""
        key = (id, sensor)
        if key in self._uid_map:
            return self._uid_map[key]
        
        self._uid_counter += 1
        uid = self._uid_counter
        self._uid_map[uid] = key
        _logger.info(f"UID: {uid} 输出成功")
        return uid

    def get_key(self, uid: int):
        key = self._uid_map.get(uid, None)
        if key is not None:
            return key
        else:
            raise ValueError(f"UID: {uid} 不存在")

    def reset(self):
        """重置 UID 生成器，用于测试或重新初始化"""
        with self._instance_lock:
            self._init_data()
        _logger.info("UID 重置成功")

global_uid = UidGenerator()

@dataclass
class CacheStructure:
    id: str
    uid: str | None
    response: str | None
    dtype: str
    data: Any
    stream: bool
    live: bool = False
    extra: dict | None = None

    def update_data(self, data: Any) -> None:
        self.data = data
        self.live = True
    @property
    def get_data(self) -> Any:
        self.live = False
        return self.data
    
class GlobalCache:
    def __init__(self):
        self._cache = LRUCache(maxsize=GlobalCacheConfig.CACHE_LEN_SIZE, getsizeof=self._getsizeof)
        self._current_ram = 0
        self._lock = threading.Lock()
        self._max_ram = GlobalCacheConfig.CACHE_RAM_SIZE
        self._mqtt_publisher = None
        self._threshold_reached = False
        
    def _getsizeof(self, item: CacheStructure) -> int:
        return len(item.data)
    def _update_cache(self, target_uid: int, old_item: Any, new_item: Any) -> None:
        """ 更新缓存并调整内存使用量 """
        old_size = self._getsizeof(old_item) if old_item else 0
        new_size = self._getsizeof(new_item)

        size_diff = new_size - old_size

        if self._current_ram + size_diff > self._max_ram * GlobalCacheConfig.OVERFLOW_THRESHOLD:
            self._overflow_handel()
            _logger.error(f' 缓存溢出：{GlobalCacheConfig.OVERFLOW_THRESHOLD * 100} % ，请合理设置缓存，或尝试减少需要缓存大小 ')

        elif self._current_ram + size_diff > self._max_ram * GlobalCacheConfig.WARNING_THRESHOLD and not self._threshold_reached:
            self._warning_handel()
            _logger.warning(f' 缓存利用率高：{GlobalCacheConfig.WARNING_THRESHOLD * 100} %，请合理设置缓存，或尝试减少需要缓存大小 ')

        while self._current_ram + size_diff > self._max_ram and self._cache:
            _, removed = self._cache.popitem()
            self._current_ram -= self._getsizeof(removed)

        if self._current_ram + size_diff <= self._max_ram:
            if target_uid in self._cache:
                self._cache[target_uid].update_data(new_item)
            else:
                self._cache[target_uid] = new_item
            self._current_ram += size_diff

    def _overflow_handel(self):
        pass
        # 停止程序避免溢出
    def _warning_handel(self):
        pass
        # 提醒用户

    def add_cache(self, buffer: CacheStructure) -> None:
        with self._lock:
            try:
                sensor_key = global_uid.get_key(buffer.uid)
                key_name = sensor_key[0] + "/" + sensor_key[1]
                old_buffer = self._cache.get(key_name, None)
                _logger.info(f' {key_name} 已被添加入缓存 ')
                self._update_cache(key_name, old_buffer, buffer)
                return True
            except Exception as e:
                _logger.error(f' 添加缓存时发生错误 {e} ')
                return False
    def get_cache(self, key: str):
        with self._lock:
            if key not in self._cache:
                _logger.info(f' {key} 缓存中不存在 ')
                return None
            else:
                return self._cache.get(key).get_data
            
    def get_cache_condition(self, key: str):
        with self._lock:
            if key not in self._cache:
                _logger.info(f' {key} 缓存中不存在 ')
                return False
            else:
                return self._cache.get(key).live

global_cache = GlobalCache()

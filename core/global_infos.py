import threading
from cachetools import LRUCache
from typing import Tuple,Any, Dict
from dataclasses import dataclass, field
import os
from loguru import logger as log
import signal

from .configs.common import GlobalCacheConfig

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, "configs", "register.json")

class ProcessPid:
    def __init__(self):
        self.pid = []

    def add(self, pid: int):
        self.pid.append(pid)

    def clear(self):
        for pid in self.pid:
            try:
                if pid and pid > 0:
                    os.kill(pid, signal.SIGTERM)
                    log.info(f"[GLOBAL]已发送终止信号到进程 {pid}")
            except ProcessLookupError:
                log.error(f"[GLOBAL]进程 {pid} 已经不存在")
            except Exception as e:
                log.error(f"[GLOBAL]终止进程 {pid} 时出错: {e}")

        self.pid.clear()
        log.info("[GLOBAL]资源清理完成")

pid = ProcessPid()

class UidGenerator:
    def __init__(self):
        self._uid_counter = 0 
        self._uid_map: Dict[Tuple[int, str], int] = {}

    def get_uid(self, id: int, sensor: str) -> int:
        key = (id, sensor)
        if key in self._uid_map:
            return self._uid_map[key]
        
        self._uid_counter += 1
        uid = self._uid_counter
        self._uid_map[uid] = key
        log.info(f"[GLOBAL]UID: {uid} 输出成功")
        return uid

    def get_key(self, uid: int):
        key = self._uid_map.get(uid, None)
        if key is not None:
            return key
        else:
            raise ValueError(f"[GLOBAL]UID: {uid} 不存在")

    def reset(self):
        with self._instance_lock:
            self._init_data()
        log.info("[GLOBAL]UID 重置成功")

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
        old_size = self._getsizeof(old_item) if old_item else 0
        new_size = self._getsizeof(new_item)

        size_diff = new_size - old_size

        if self._current_ram + size_diff > self._max_ram * GlobalCacheConfig.OVERFLOW_THRESHOLD:
            self._overflow_handel()
            log.error(f' [GLOBAL]缓存溢出：{GlobalCacheConfig.OVERFLOW_THRESHOLD * 100} % ，请合理设置缓存，或尝试减少需要缓存大小 ')

        elif self._current_ram + size_diff > self._max_ram * GlobalCacheConfig.WARNING_THRESHOLD and not self._threshold_reached:
            self._warning_handel()
            log.warning(f' [GLOBAL]缓存利用率高：{GlobalCacheConfig.WARNING_THRESHOLD * 100} %，请合理设置缓存，或尝试减少需要缓存大小 ')

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
 
    def _warning_handel(self):
        pass

    def add_cache(self, buffer: CacheStructure) -> None:
        with self._lock:
            try:
                sensor_key = global_uid.get_key(buffer.uid)
                key_name = sensor_key[0] + "/" + sensor_key[1]
                old_buffer = self._cache.get(key_name, None)
                log.info(f' [GLOBAL] {key_name} 已被添加入缓存 ')
                self._update_cache(key_name, old_buffer, buffer)
                return True
            except Exception as e:
                log.error(f'[GLOBAL] 添加缓存时发生错误 {e} ')
                return False
    def get_cache(self, key: str):
        with self._lock:
            if key not in self._cache:
                log.info(f'[GLOBAL] {key} 缓存中不存在 ')
                return None
            else:
                return self._cache.get(key).get_data
            
    def get_cache_condition(self, key: str):
        with self._lock:
            if key not in self._cache:
                log.info(f'[GLOBAL] {key} 缓存中不存在 ')
                return False
            else:
                return self._cache.get(key).live

global_cache = GlobalCache()

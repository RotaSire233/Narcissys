import threading
from typing import Tuple, Union, Any, Optional, ClassVar, Dict
from dataclasses import dataclass, field
from enum import Enum
import logging
from .configs import *
from cachetools import LRUCache
from abc import ABC, abstractmethod
from utils.datastruct.chain import ChunkChain
from loguru import logger as _logger
from collections import OrderedDict

__all__ = ['StaticBufferStruct',
           'StreamBufferStruct',
           'StaticCache'
           'StreamCache'
           ]


# 缓存配置项目
DEFAULT_STATIC_CACHE_LEN_SIZE = UdpConfigs.DEFAULT_STATIC_CACHE_LEN_SIZE
DEFAULT_STATIC_CACHE_RAM_SIZE = UdpConfigs.DEFAULT_STATIC_CACHE_RAM_SIZE
DEFAULT_STREAM_CACHE_LEN_SIZE = UdpConfigs.DEFAULT_STREAM_CACHE_LEN_SIZE
DEFAULT_STREAM_CACHE_RAM_SIZE = UdpConfigs.DEFAULT_STREAM_CACHE_RAM_SIZE

# 活跃节点超时配置项目
DEFAULT_CLEAN_INTERVAL = UdpConfigs.DEFAULT_CLEAN_INTERVAL

# 尚未加入chunk验证
@dataclass(frozen=True)
class StaticBufferStruct:
    """静态数据缓冲区"""
    id: hex
    uid: int
    name: str
    addr: Tuple[str, int]
    timestamp: int
    data: Any
    rout: str
    dtype: str = "static"
    def __init__(self):
        _logger.debug(f' {self.uid}(static): 数据块添加成功 ')

@dataclass(frozen=True)
class StreamBufferStruct:
    """流式数据缓冲区"""
    addr: Tuple[str, int]
    id: hex
    uid: int
    name: str
    timestamp: int
    rout: str
    current_chunk: int = 0x0000
    end_chunk: int = 0xffff
    done: bool = False
    chunks: OrderedDict = field(default_factory=OrderedDict)
    
    def add_chunk(self, chunk: bytes, chunk_id: int) -> bool:
        """
        将缓存数据添加到有序字典中
        返回值表示是否成功添加
        """
        if chunk_id == self.current_chunk:
            self.chunks[chunk_id] = chunk
            self.current_chunk += 0x0001
            self.done = self.current_chunk >= self.end_chunk
            _logger.debug(f' {self.uid}(stream): 数据块 {chunk_id} 添加成功 ')
            return True
        return False
    def get_chunk(self, chunk_id: int) -> Optional[bytes]:
        """随机访问特定chunk"""
        return self.chunks.get(chunk_id)
    @property
    def get_full_data(self) -> bytes:
        """按顺序拼接所有的数据"""
        return b"".join(self.chunks.values())
    
    @property
    def is_complete(self) -> bool:
        """检查是否所有chunk都已接收"""
        expected_chunks = self.end_chunk - 0x0000
        return len(self.chunks) == expected_chunks and self.done
    @property
    def get_chunks_count(self) -> int:
        """获取已接收的chunk数量"""
        return len(self.chunks)
    @property
    def get_latest_chunk(self) -> Optional[bytes]:
        """ 返回最新的chunk """
        if not self.chunks:
            return None
        
        latest_key = next(reversed(self.chunks))
        return self.chunks[latest_key]
    def get_next_chunk(self) -> Optional[bytes]:
        """
        迭代获取数据，每次调用返回下一个chunk
        """
        if not hasattr(self, '_iter_index'):
            self._iter_index = 0
            
        if self._iter_index < len(self.chunks):
            chunk_key = list(self.chunks.keys())[self._iter_index]
            chunk_data = self.chunks[chunk_key]
            self._iter_index += 1
            return chunk_data
        else:
            if self.done:
                self._iter_index = 0
            return None
            
    def reset_chunk_iterator(self) -> None:
        """
        重置迭代器索引
        """
        self._iter_index = 0

    def __len__(self) -> int:
        """返回所有chunks的总byte"""
        return sum(len(chunk) for chunk in self.chunks.values())
    
@dataclass(frozen=True)
class FltStruct:
    """ 流式文本数据结构 """
    id: hex
    uid: int
    addr: Tuple[str, int]
    name: str
    timestamp: int
    rout: str

    stream_length: int
    datas: StreamBufferStruct
    dtype: str = "flt"
    
    
   
@dataclass(frozen=True)
class AudStruct:
    """ 音频数据结构 """
    id: hex
    uid: int
    addr: Tuple[str, int]
    name: str
    timestamp: int
    rout: str

    formats: str
    sample_rate: int
    bit_depth: int
    channels: int
    datas: StreamBufferStruct
    dtype: str = "aud"
    

@dataclass(frozen=True)
class ImgStruct:
    """ 图片数据结构 """
    id: hex
    uid: int
    addr: Tuple[str, int]
    name: str
    timestamp: int
    rout: str

    formats: str
    size: Tuple[int, int]
    datas: StreamBufferStruct
    dtype: str = "img"
    
class BaseCache(ABC):
    """缓存方法基类"""
    def __init__(self,
                 max_len: int,
                 max_ram: int):
        self._cache = LRUCache(maxsize=max_len, getsizeof=self._getsizeof)
        self._current_ram = 0
        self._lock = threading.Lock()
        self._max_ram = max_ram
    @abstractmethod
    def _getsizeof(self, item: Any) -> int:
        """获取缓存对象大小（子类必须实现此方法）"""
        pass
    @abstractmethod
    def add(self, item: Any) -> None:
        """添加缓存对象（子类必须实现此方法）"""
        pass
    
    def get_by_id(self, id: hex) -> Optional[Any]:
        """通过ID获取缓存对象"""
        with self._lock:
            return self._cache.get(id)
    
    def remove_by_id(self, target_id: hex) -> None:
        """删除指定ID的缓存项"""
        with self._lock:
            if target_id in self._cache:
                removed = self._cache.pop(target_id)
                self._current_ram -= self._getsizeof(removed)
    
    
class StaticCache(BaseCache):
    """静态数据缓存"""
    def __init__(self, 
                 max_len: int = DEFAULT_STATIC_CACHE_LEN_SIZE,
                 max_ram: int = DEFAULT_STATIC_CACHE_RAM_SIZE):
        super().__init__(max_len, max_ram)

    def _getsizeof(self, item: 'StaticBufferStruct') -> int:
        return len(item.data)
    def _update_cache(self, target_uid: int, old_item: Any, new_item: Any) -> None:
        """ 更新缓存并调整内存使用量 """
        old_size = self._getsizeof(old_item) if old_item else 0
        new_size = self._getsizeof(new_item)

        size_diff = new_size - old_size

        while self._current_ram + size_diff > self._max_ram and self._cache:
            _, removed = self._cache.popitem()
            self._current_ram -= self._getsizeof(removed)

        if self._current_ram + size_diff <= self._max_ram:
            self._cache[target_uid] = new_item
            self._current_ram += size_diff

    def add(self, buffer: 'StaticBufferStruct') -> None:
        with self._lock:
            current_buffer = self._cache.get(buffer.id)
            _logger.info(f' {buffer.uid} 已被添加入缓存 ')
            self._update_cache(buffer.uid, current_buffer, buffer)
    def get_cache(self, uid: int):
        with self._lock:
            if uid not in self._cache:
                _logger.warning(f' {uid} 缓存中不存在 ')
                return None
            else:
                return self._cache.get(uid)
    def get_all_data(self) -> dict:
        """获取所有缓存中的数据"""
        with self._lock:
            return dict(self._cache)

class StreamCache(BaseCache):
    """流数据缓存"""
    def __init__(self, 
                 max_len: int = DEFAULT_STREAM_CACHE_LEN_SIZE,
                 max_ram: int = DEFAULT_STREAM_CACHE_RAM_SIZE):
        super().__init__(max_len, max_ram)

    def _getsizeof(self, item: 'StreamBufferStruct') -> int:
        return len(item.datas)

    def _update_cache(self, target_uid: int, old_item: Any, new_item: Any) -> None:
        """ 更新缓存并调整内存使用量 """
        old_size = self._getsizeof(old_item) if old_item else 0
        new_size = self._getsizeof(new_item)

        size_diff = new_size - old_size

        while self._current_ram + size_diff > self._max_ram and self._cache:
            _, removed = self._cache.popitem()
            self._current_ram -= self._getsizeof(removed)

        if self._current_ram + size_diff <= self._max_ram:

            if isinstance(new_item, StreamBufferStruct) and new_item.chunks is not None:
                current = new_item.chunks
                while current.next:
                    current = current.next
                
                if old_item and isinstance(old_item, StreamBufferStruct) and old_item.chunks is not None:
                    current.next = old_item.chunks
            
            self._cache[target_uid] = new_item
            self._current_ram += size_diff
    def init_stream(self, buffer: FltStruct | AudStruct | ImgStruct ) -> None:
        with self._lock:
            self._cache[buffer.uid] = buffer
            _logger.info(f' {buffer.uid} 已在缓存中被初始化 ')

    def add(self, buffer: 'StreamBufferStruct') -> None:
        with self._lock:
            current_buffer = self._cache.get(buffer.uid).datas
            _logger.info(f' {buffer.uid} 已被添加入缓存 ')
            self._update_cache(buffer.uid, current_buffer, buffer)

    def get_cache(self, uid: int):
        with self._lock:
            if uid not in self._cache:
                _logger.warning(f' {uid} 缓存中不存在 ')
                return None
            else:
                return self._cache.get(uid)
                
    def get_all_data(self) -> dict:
        """获取所有缓存中的数据"""
        with self._lock:
            return dict(self._cache)

            

    

    

    



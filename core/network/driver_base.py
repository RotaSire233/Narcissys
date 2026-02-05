import asyncio
import platform
import traceback
from typing import Optional, Callable, Any, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod
from loguru import logger as log
from .udp.udp import UdpProtocol
from .tcp.tcp import TcpProtocol
from .rtp.rtp import RtpProtocol

class CountMinSketch:
    def __init__(self, width=1024, depth=4):
        self.width = width
        self.depth = depth
        self.table = [[0] * width for _ in range(depth)]
        self.seeds = [113, 137, 179, 191][:depth]  # 哈希函数种子
    
    def _hash(self, item, seed):
        """计算元素的哈希值"""
        return hash(str(item) + str(seed)) % self.width
    
    def increment(self, item):
        """增加元素的频率计数"""
        for i in range(self.depth):
            idx = self._hash(item, self.seeds[i])
            self.table[i][idx] += 1
    
    def estimate(self, item):
        """估计元素的频率"""
        min_count = float('inf')
        for i in range(self.depth):
            idx = self._hash(item, self.seeds[i])
            min_count = min(min_count, self.table[i][idx])
        return min_count
    
    def reset(self):
        """重置频率统计"""
        self.table = [[0] * self.width for _ in range(self.depth)]

class ServerCache():
    def __init__(self, 
                 max_size: int,
                 window_ratio: float,
                 sketch_width: int = 1024,
                 sketch_depth: int = 4
                 ):
        self.max_size = max_size
        self.window_size = int(max_size * window_ratio)
        self.main_size = max_size - self.window_size
        
        self.sketch = CountMinSketch(width=sketch_width, depth=sketch_depth)
        self.window_cache = {}
        self.window_order = []

        self.main_cache = {}
        self.frequency_order = {}
        self.min_frequency = 1

    def _update_window_order(self, key):
        if key in self.window_order:
            self.window_order.remove(key)
        self.window_order.append(key)

    def _update_main_frequency(self, key):
        if key not in self.main_cache:
            return
        old_freq = self.main_cache[key][1]
        new_freq = old_freq + 1

        self.main_cache[key] = (self.main_cache[key][0], new_freq)

        self.frequency_order[new_freq].remove(key)
        if not self.frequency_order[old_freq]:
            del self.frequency_order[old_freq]
            if self.min_frequency == old_freq:
                self.min_frequency += 1
        
        if new_freq not in self.frequency_order:
            self.frequency_order[new_freq] = set()
        self.frequency_order[new_freq].add(key)

    def _evict_from_window(self):
        if not self.window_order:
            return
        evict_key = self.window_order.pop(0)
        if evict_key in self.window_cache:
            del self.window_cache[evict_key]
    
    def _evict_from_main(self):
        if not self.frequency_order or self.min_frequency not in self.frequency_order:
            return
        
        min_freq_keys = self.frequency_order[self.min_frequency]
        if not min_freq_keys:
            return
        
        evict_key = min_freq_keys.pop()
        if not min_freq_keys:
            del self.frequency_order[self.min_frequency]
            self.min_frequency += 1
        
        if evict_key in self.main_cache:
            del self.main_cache[evict_key]
    
    def _add_to_main(self, key, value):
        if len(self.main_cache) >= self.main_size:
            self._evict_from_main()
        
        initial_freq = 1
        self.main_cache[key] = (value, initial_freq)

        if initial_freq not in self.frequency_order:
            self.frequency_order[initial_freq] = set()
        self.frequency_order[initial_freq].add(key)
        self.min_frequency = min(self.min_frequency, initial_freq)
    
    def put(self, key, value):
        if key in self.main_cache:
            self.main_cache[key] = (value, self.main_cache[key][1])
            self._update_main_frequency(key)
            self.sketch.increment(key)
            return
        
        if key in self.window_cache:
            self.window_cache[key] = (value, self.window_cache[key][1])
            self._update_window_order(key)
            self.sketch.increment(key)
            return
        
        if len(self.window_cache) >= self.window_size:
            self._evict_from_window()

        import time
        self.window_cache[key] = (value, time.time())
        self.window_order.append(key)
        self.sketch.increment(key)

    def get(self, key):
        if key in self.main_cache:
            value, _ = self.main_cache[key]
            self._update_main_frequency(key)
            self.sketch.increment(key)
            return value
        
        if key in self.window_cache:
            value, _ = self.window_cache.pop(key)
            self.window_order.remove(key)

            self._add_to_main(key, value)
            self.sketch.increment(key)
            return value
        
        return None
    
    def __contains__(self, key):
        return key in self.main_cache or key in self.window_cache
    
    def __len__(self):
        return len(self.main_cache) + len(self.window_cache)
    
    def clear(self):
        self.window_cache.clear()
        self.window_order.clear()
        self.main_cache.clear()
        self.frequency_order.clear()
        self.min_frequency = 1
        self.sketch.reset()

    def get_stats(self):
        return {
            'total_size': len(self),
            'max_size': self.max_size,
            'window_size': len(self.window_cache),
            'main_size': len(self.main_cache),
            'min_frequency': self.min_frequency,
            'frequency_levels': len(self.frequency_order)
        }

class DriverBase(ABC):
    def __init__(self, 
                 ip: str,
                 port: int,
                 name: str,
                 socket_type: str,
                 max_thread: int = 8,
                 max_cache_size: int = 80 * 1024 * 1024,
                 window_ratio: float = 0.2
                 ):
        if socket_type not in ["udp", "tcp", "rtp"]:
            raise ValueError(f"socket must be 'udp', 'tcp' or 'rtp', not {socket_type}")
        self.socket_type = socket_type

        self.ip = ip
        self.port = port
        self.key_root = str(port) + '/'
        self.tag = f"[NetDriver][{name}]:"
        self._max_thread = max_thread
        self._cache = ServerCache(max_size=max_cache_size, window_ratio=window_ratio)
        self._stack = []

        self.running = False
        self._executor = None
        self._loop = asyncio.get_event_loop()
        
        self._transport = None
        self._protocol = None
        self._connected_clients = {} 
        self._recv_queue = asyncio.Queue()
    
    async def start(self) -> None:
        if self.running:
            log.warning(f"{self.tag} Socket已经在运行中")
            return
        
        try:
            self.running = True
            await self._setup()
            log.info(f"{self.tag} Socket服务启动成功，监听 {self.ip}:{self.port}")
        except Exception as e:
            log.error(f"{self.tag} Socket服务启动失败: {e}")
            log.debug(traceback.format_exc())
            self.running = False
            raise
    
    async def stop(self) -> None:
        if not self.running:
            log.warning(f"{self.tag} Socket已经停止")
            return
        
        try:
            self.running = False
            await self._cleanup()
            
            if self._executor:
                self._executor.shutdown(wait=False) 
                log.debug(f"{self.tag} 线程池已关闭")
                self._executor = None
            
            log.info(f"{self.tag} Socket服务停止成功")
        except Exception as e:
            log.error(f"{self.tag} Socket服务停止失败: {e}")
            log.debug(traceback.format_exc())
            raise

    @property
    def executor(self) -> ThreadPoolExecutor:
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=self._max_thread,
                thread_name_prefix=f"{self.tag}_pool"
            )
            log.debug(f"{self.tag} 创建线程池，最大工作线程数: {self._max_thread}")
        return self._executor
    
    async def run_task(self, func: Callable, *args, **kwargs) -> Any:
        return await self._loop.run_in_executor(self.executor, func, *args, **kwargs)
    
    async def _setup(self) -> None:
        if self.socket_type == "udp":        
            self._protocol = UdpProtocol(self)
            self._transport, _ = await self._loop.create_datagram_endpoint(
                lambda: self._protocol,
                local_addr=(self.ip, self.port)
            )
        elif self.socket_type == "tcp":
            self._protocol = TcpProtocol(self)
            self._transport, _ = await self._loop.create_server(
                lambda: self._protocol,
                self.ip, self.port
            )
            log.info(f"{self.tag} TCP服务已启动, 监听 {self.ip}:{self.port}")
        else:
            self._protocol = RtpProtocol(self)
            log.info(f"{self.tag} RTP服务已启动, 监听 {self.ip}:{self.port}")
    
    async def _cleanup(self) -> None:
        if self._transport:
            if self.socket_type == "tcp":
                self._transport.close()
            else:
                self._transport.close()
            self._transport = None
        
        self._protocol = None
        self._connected_clients.clear()

        while not self._recv_queue.empty():
            try:
                self._recv_queue.get_nowait()
                self._recv_queue.task_done()
            except asyncio.QueueEmpty:
                break
    
    async def send(self, data: bytes, addr: Optional[Tuple[str, int]] = None) -> None:
        if not self.running:
            raise RuntimeError(f"{self.tag} 服务未运行")
        
        if self.socket_type == "udp":
            if not addr:
                raise ValueError(f"{self.tag} UDP发送必须提供地址")
            self._transport.sendto(data, addr)
        else:
            if addr:
                if addr in self._connected_clients:
                    self._connected_clients[addr].write(data)
                else:
                    raise ConnectionError(f"{self.tag} 客户端 {addr} 未连接")
            else:
                for transport in self._connected_clients.values():
                    transport.write(data)
    
    async def recv(self) -> Tuple[bytes, Optional[Tuple[str, int]]]:
        if not self.running:
            raise RuntimeError(f"{self.tag} 服务未运行")
        
        return await self._recv_queue.get()
    
    async def data_received(self, data: bytes, addr: Tuple[str, int]):
        """接收到数据时调用"""
        pass
    
    async def connection_made(self, transport):
        """TCP客户端连接建立时调用"""
        pass
    
    async def connection_lost(self, addr: Tuple[str, int], exc):
        """TCP客户端连接丢失时调用"""
        pass
    
    def is_running(self) -> bool:
        return self.running
    
    def get_address(self) -> Tuple[str, int]:
        return (self.ip, self.port)
    
    def __del__(self):
        if self.running:
            self.running = False
            if self._executor:
                try:
                    self._executor.shutdown(wait=False)
                    self._executor = None
                except:
                    pass
            if hasattr(self, '_loop') and not self._loop.is_closed():
                try:
                    self._loop.close()
                except:
                    pass
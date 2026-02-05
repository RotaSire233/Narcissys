import asyncio
from loguru import logger as log
from typing import Optional, Set, Dict, Final
import socket
from dataclasses import dataclass
import threading

    

LISTEN_PORT_RANGE: Final[tuple[int, int]] = (1025, 1225)
MAX_CACHE_SIZE = 80 * 1024 * 1024
REDIS_LINE = 64 * 1024 * 1024 

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
    
LOCAL_IP = get_local_ip()

class PortPool():
    def __init__(self):
        self._allocated_ports: Set[int] = set()
        self._port_pools: Dict[str, dict] = {}
        self._instance_lock = threading.Lock()

    def register_range(self, start: int, end: int):  
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
        with self._instance_lock:
            for range_key, pool in self._port_pools.items():
                start = pool["start"]
                end = pool["end"]
                current = pool["current"]
                freed = pool["freed"]

                if freed:
                    port = freed.pop(0)
                    if start <= port <= end and port not in self._allocated_ports:
                        self._allocated_ports.add(port)
                        log.info(f"[NETWORK]获取端口成功: {port}")
                        return port

                while current <= end:
                    if current not in self._allocated_ports:
                        self._allocated_ports.add(current)
                        pool["current"] = current + 1
                        log.info(f"[NETWORK]获取端口成功: {current}")
                        return current
                    current += 1

                pool["current"] = end + 1
                log.info("[NETWORK]端口已满")
            return None

    def release_port(self, port: int):
        if port not in self._allocated_ports:
            log.warning(f"[NETWORK]释放一个未分配的端口: {port}")
            return

        with self._instance_lock:
            self._allocated_ports.discard(port)
            log.info(f"释放端口 {port}")

            for range_key, pool in self._port_pools.items():
                start = pool["start"]
                end = pool["end"]
                if start <= port <= end:
                    pool["freed"].append(port)
                    pool["freed"].sort()
                    break

    def has_port(self, port: int) -> bool:
        return port in self._allocated_ports

    def reset(self):
        with self._instance_lock:
            self.__init__()
        log.debug(f"[NETWORK]重置端口池")

PORT_POOL = PortPool()
PORT_POOL.register_range(*LISTEN_PORT_RANGE)

class ServerManager:
    def __init__(self):
        self.servers = {}
        self.tasks = {}
        self._lock = asyncio.Lock()

    async def create_driver(self,
                            driver: Optional[asyncio.Protocol],
                            name: str,
                            dtype: str):
        async with self._lock:
           port = driver.port
           if port in self.servers:
               log.error(f"[NETWORK]端口 {port} 被重复申请")
               return None
           
           self.servers[port] = {
               "driver": driver,
               "dtype": dtype,
               "name": name
           }

           task = asyncio.create_task(driver.run(), name=f"{dtype}_{port}")
           self.tasks[port] = task

           return port
        
    async def stop_driver(self, port: int):
        async with self._lock:
            if port not in self.servers:
                log.error(f"[NETWORK]端口 {port} 未申请")
                return
            
            driver = self.servers[port]["driver"]
            driver.stop()
            
            if port in self.tasks:
                task = self.tasks[port]
                if not task.done():
                    task.cancel()
            
            del self.servers[port]
            if port in self.tasks:
                del self.tasks[port]
            
            PORT_POOL.release_port(port)
            log.info(f"[NETWORK]已停止端口 {port} 的服务器")

    async def stop_all_drivers(self):
        async with self._lock:
            for port in list(self.servers.keys()):
                try:
                    await self.stop_driver(port)
                except Exception as e:
                    log.error(f"[NETWORK]停止端口 {port} 的服务器时出错: {e}")

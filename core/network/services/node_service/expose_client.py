import asyncio
import json
import socket
from typing import Optional, Callable
from loguru import logger as _logger
from ...net_manager import get_local_ip

class UdpExposeClient:
    def __init__(
        self,
        broadcast_port: int = 1226,
        broadcast_interval: int = 10,
        broadcast_address: str = "255.255.255.255"
    ):
        self.broadcast_port = broadcast_port
        self.broadcast_interval = broadcast_interval
        self.broadcast_address = broadcast_address
        self.local_ip = get_local_ip()
        self.sock: Optional[socket.socket] = None
        self.broadcast_task: Optional[asyncio.Task] = None
        self.running = False
        self.on_broadcast_callback: Optional[Callable] = None
        
    def set_broadcast_callback(self, callback: Callable):
        self.on_broadcast_callback = callback
        
    async def start_broadcasting(self):

        if self.running:
            _logger.warning("[NODE_SERVICE]: UDP广播客户端已在运行中")
            return
            
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.setblocking(False)
            
            self.running = True
            self.broadcast_task = asyncio.create_task(self._broadcast_loop())
            _logger.info(f"[NODE_SERVICE]: UDP广播客户端已启动，广播地址: {self.broadcast_address}:{self.broadcast_port}")
            
        except Exception as e:
            _logger.error(f"[NODE_SERVICE]: 启动UDP广播客户端失败: {e}")
            self.running = False
            if self.sock:
                self.sock.close()
                self.sock = None
                
    async def stop_broadcasting(self):

        self.running = False
        
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                pass
            self.broadcast_task = None
            
        if self.sock:
            self.sock.close()
            self.sock = None
            
        _logger.info("[NODE_SERVICE]: UDP广播客户端已停止")
        
    async def _broadcast_loop(self):

        while self.running:
            try:
                await self._send_broadcast()

                await asyncio.sleep(self.broadcast_interval)
                
            except Exception as e:
                _logger.error(f"[NODE_SERVICE]: 广播过程中出错: {e}")
                await asyncio.sleep(self.broadcast_interval)
                
    async def _send_broadcast(self):
        if not self.sock or not self.running:
            return
            
        try:
            discovery_message = {
                "service": "nar/sys",
                "port": 1883,
                "timestamp": asyncio.get_event_loop().time()
            }
            
            message_json = json.dumps(discovery_message)
            message_bytes = message_json.encode('utf-8')

            self.sock.sendto(
                message_bytes, 
                (self.broadcast_address, self.broadcast_port)
            )
            
            _logger.info(f"[NODE_SERVICE]: 已广播系统发现消息: {discovery_message}")
            

            if self.on_broadcast_callback:
                try:
                    self.on_broadcast_callback(discovery_message)
                except Exception as e:
                    _logger.error(f"[NODE_SERVICE]: 广播回调函数执行出错: {e}")
                    
        except Exception as e:
            _logger.error(f"[NODE_SERVICE]: 发送广播消息失败: {e}")


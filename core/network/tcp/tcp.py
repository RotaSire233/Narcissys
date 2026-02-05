import asyncio
from loguru import logger as log


class TcpProtocol(asyncio.Protocol):
    def __init__(self, driver):
        self.driver = driver
        self.peername = None
                
    def connection_made(self, transport):
        self.peername = transport.get_extra_info('peername')
        self.driver._connected_clients[self.peername] = transport
        self.driver._transport = transport
        log.info(f"{self.driver.tag} TCP客户端已连接: {self.peername}")
        asyncio.create_task(self.driver.connection_made(transport))
                
    def data_received(self, data):
        asyncio.create_task(self.driver._recv_queue.put((data, self.peername)))
        asyncio.create_task(self.driver.data_received(data, self.peername))
                
    def connection_lost(self, exc):
        if self.peername in self.driver._connected_clients:
            del self.driver._connected_clients[self.peername]
                
        if exc:
            log.error(f"{self.driver.tag} TCP连接丢失: {self.peername}, 错误: {exc}")
        else:
            log.info(f"{self.driver.tag} TCP客户端已断开: {self.peername}")
        asyncio.create_task(self.driver.connection_lost(self.peername, exc))

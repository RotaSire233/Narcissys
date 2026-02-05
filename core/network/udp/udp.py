import asyncio

from loguru import logger as log

class UdpProtocol(asyncio.DatagramProtocol):
                def __init__(self, driver):
                    self.driver = driver
                
                def connection_made(self, transport):
                    self.driver._transport = transport
                    log.info(f"{self.driver.tag} UDP服务已启动,监听 {self.driver.ip}:{self.driver.port}")
                
                def datagram_received(self, data, addr):
                    asyncio.create_task(self.driver._recv_queue.put((data, addr)))
                    asyncio.create_task(self.driver.data_received(data, addr))
                
                def error_received(self, exc):
                    log.error(f"{self.driver.tag} UDP错误: {exc}")
                
                def connection_lost(self, exc):
                    if exc:
                        log.error(f"{self.driver.tag} UDP连接丢失: {exc}")
                    else:
                        log.info(f"{self.driver.tag} UDP连接已关闭")
            
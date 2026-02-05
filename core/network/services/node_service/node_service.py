import asyncio
from typing import Optional, Dict, Any, Tuple
from loguru import logger as log
import traceback

from .configs import NodeConfigs
from .protocol import RequestType, DefaultProtocolHeader
from ...driver_base import DriverBase
from ...net_manager import LOCAL_IP


class NodeService(DriverBase):
    def __init__(self, port: int):
        super().__init__(ip=LOCAL_IP,
                         port=port,
                         name="NodeService",
                         max_thread=NodeConfigs.MAX_WORKERS,
                         max_cache_size=NodeConfigs.BUFFER_SIZE)
        self.header = DefaultProtocolHeader()
        self.request = RequestType

    async def data_received(self, data: bytes, addr: Tuple[str, int]):
        try:
            await self._handle_data(data, addr)
        except Exception as e:
            log.error(f"{self.tag} 处理数据失败: {e}")
            log.debug(traceback.format_exc())

    async def _handle_data(self, data: bytes, addr: Tuple[str, int]):
        header = data[:len(self.header)]
        payload = data[len(self.header):]
        protocol_header = self.header.decode_method(header)
        decode_func = self.request.get_decoder(
                    channel=protocol_header.channel,
                    port=protocol_header.port,
                    decode=protocol_header.decode
                )
        encoded_data = await self._loop.run_in_executor(
                    self._executor,
                    decode_func,
                    payload
                )
        log.info(f"{self.tag} 从 {addr} 接收到数据: {data.hex()}")
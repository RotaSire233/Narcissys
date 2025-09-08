import socket
from typing import Tuple
from loguru import logger as _logger
import json
import asyncio
from dataclasses import dataclass



@dataclass(frozen=True)
class UdpTypeStatic:
    INT = "int"
    FLO = "float"
    STR = "string"

@dataclass(frozen=True)
class UdpTypeStream:
    STR = "string"
    IMG = "image"
    AUD = "audio"


class _RequestStruct:
    """ 请求类型和结构配置 """
    def __init__(self, channel: int, port: int, decode: int):
        self.channel = channel
        self.port = port
        self.decode = decode
    @property
    def to_bytes(self) -> bytes:
        """将结构编码为字节序列"""
        return bytes([self.channel, self.port, self.decode])



@dataclass(frozen=True)
class RequestType:
    FIN = _RequestStruct(channel=0x00, port=0x00, decode=0x00)   # 搜索包
    HEA = _RequestStruct(channel=0x00, port=0x00, decode=0x01)   # 心跳包
    STO = _RequestStruct(channel=0x00, port=0x00, decode=0x02)   # 停止包
    FLO = _RequestStruct(channel=0x01, port=0x00, decode=0x10)   # 浮点数
    INT = _RequestStruct(channel=0x01, port=0x00, decode=0x11)   # 整数
    STR = _RequestStruct(channel=0x01, port=0x00, decode=0x12)   # 字符串

    FLT_I = _RequestStruct(channel=0x01, port=0x00, decode=0x13)   # 流式文本初始化
    AUD_I = _RequestStruct(channel=0x01, port=0x00, decode=0x14)   # 音频初始化
    IMG_I = _RequestStruct(channel=0x01, port=0x00, decode=0x15)   # 图片初始化
    FLT = _RequestStruct(channel=0x01, port=0x01, decode=0x13)   # 流式文本
    AUD = _RequestStruct(channel=0x01, port=0x01, decode=0x14)   # 音频
    IMG = _RequestStruct(channel=0x01, port=0x01, decode=0x15)   # 图片

class UdpClientDriver:
    def __init__(self,):
        self.mqtt_addr: str = None
        self.finding = True
        self.broadcast_port: int = 1226
        self._send_sock: socket.socket = None
        self._periodic_tasks = {}
        self._stream_tasks = {}
    # 监听广播获取暴露的地址
    def listen_for_broadcast(self, buffer_size=1024):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.bind(('', self.broadcast_port))
        
        _logger.info(f"开始监听端口 {self.broadcast_port} 的UDP广播消息...")
        
        try:
            while self.finding:
                # 设置超时以便能够响应中断
                sock.settimeout(1.0)
                # 接收数据
                try:
                    data, addr = sock.recvfrom(buffer_size)
                    if data:
                        json_data: dict = self.decode_broadcast_message(data)
                        if json_data:
                            if json_data.get("service", False) == "nar/sys" and json_data.get("port", False):
                                broker_addr = addr[0]
                                broker_port = json_data.get("port")
                                self.finding = False
                            return broker_addr, broker_port
                except socket.timeout:
                    # 超时继续循环，以便检查 self.finding 状态
                    continue

        except KeyboardInterrupt:
            _logger.info("监听已停止")
        finally:
            sock.close()
    @staticmethod
    def decode_broadcast_message(data: bytes):
        """ 解码广播消息 """

        message_str = data.decode('utf-8')
        message_dict = json.loads(message_str)
        return message_dict
    
    def initialize_sender(self):
        """初始化用于发送的socket"""
        if self._send_sock is None:
            self._send_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._send_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            _logger.info("发送UDP socket初始化完成")

    async def send_async(self, data: bytes, addr: Tuple[str, int]):
        """
        异步发送UDP数据包
        
        Args:
            data: 要发送的数据
            addr: 目标地址 (ip, port)
        """
        # 确保发送socket已初始化
        if self._send_sock is None:
            self.initialize_sender()
            
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._send_sock.sendto, data, addr)
        _logger.info(f"已异步发送 {len(data)} 字节数据到 {addr}")

    def close_sender(self):
        """关闭发送socket"""
        if self._send_sock:
            self._send_sock.close()
            self._send_sock = None
            _logger.info("发送UDP socket已关闭")
            
    def start_periodic_send(self, task_id: str, data: bytes, addr: Tuple[str, int], interval: float):
        """
        启动定期发送任务
        
        Args:
            task_id: 任务ID
            data: 要发送的数据
            addr: 目标地址 (ip, port)
            interval: 发送间隔（秒）
        """
        if task_id in self._periodic_tasks:
            _logger.warning(f"定期发送任务 {task_id} 已存在")
            return
            
        async def _periodic_send_task():
            while True:
                try:
                    await self.send_async(data, addr)
                    await asyncio.sleep(interval)
                except asyncio.CancelledError:
                    _logger.info(f"定期发送任务 {task_id} 已取消")
                    break
                except Exception as e:
                    _logger.error(f"定期发送任务 {task_id} 出错: {e}")
        
        self._periodic_tasks[task_id] = asyncio.create_task(_periodic_send_task())
        _logger.info(f"已启动定期发送任务 {task_id}，间隔 {interval} 秒")
        
    def stop_periodic_send(self, task_id: str):
        """ 停止定期发送任务 """
        if task_id in self._periodic_tasks:
            self._periodic_tasks[task_id].cancel()
            del self._periodic_tasks[task_id]
            _logger.info(f"已停止定期发送任务 {task_id}")
        else:
            _logger.warning(f"定期发送任务 {task_id} 不存在")
            
    def stop_all_periodic_sends(self):
        """停止所有定期发送任务"""
        for task_id in list(self._periodic_tasks.keys()):
            self.stop_periodic_send(task_id)

    async def send_stream_data(self, data: bytes, addr: Tuple[str, int]):
        """
        发送流式数据
        
        Args:
            data: 要发送的流式数据
            addr: 目标地址 (ip, port)
        """
        await self.send_async(data, addr)
        _logger.debug(f"已发送流式数据，大小: {len(data)} 字节")

    def start_stream_send(self, task_id: str, data_queue: asyncio.Queue, addr: Tuple[str, int]):
        """
        启动流式数据发送任务
        
        Args:
            task_id: 任务ID
            data_queue: 包含待发送数据的队列
            addr: 目标地址 (ip, port)
        """
        if task_id in self._stream_tasks:
            _logger.warning(f"流式发送任务 {task_id} 已存在")
            return
            
        async def _stream_send_task():
            try:
                while True:
                    # 从队列中获取数据并发送
                    data = await data_queue.get()
                    if data is None:  # 特殊值表示结束
                        _logger.info(f"流式发送任务 {task_id} 收到结束信号")
                        break
                    await self.send_stream_data(data, addr)
                    data_queue.task_done()
            except asyncio.CancelledError:
                _logger.info(f"流式发送任务 {task_id} 已取消")
            except Exception as e:
                _logger.error(f"流式发送任务 {task_id} 出错: {e}")
        
        self._stream_tasks[task_id] = asyncio.create_task(_stream_send_task())
        _logger.info(f"已启动流式发送任务 {task_id}")

    def stop_stream_send(self, task_id: str):
        """停止流式数据发送任务"""
        if task_id in self._stream_tasks:
            self._stream_tasks[task_id].cancel()
            del self._stream_tasks[task_id]
            _logger.info(f"已停止流式发送任务 {task_id}")
        else:
            _logger.warning(f"流式发送任务 {task_id} 不存在")

    def stop_all_stream_sends(self):
        """停止所有流式数据发送任务"""
        for task_id in list(self._stream_tasks.keys()):
            self.stop_stream_send(task_id)

    async def add_stream_data(self, task_id: str, data: bytes, data_queue: asyncio.Queue):
        """
        向流式任务添加数据
        
        Args:
            task_id: 流式任务ID
            data: 要发送的数据
            data_queue: 数据队列
        """
        if task_id not in self._stream_tasks:
            _logger.warning(f"流式任务 {task_id} 不存在")
            return
            
        await data_queue.put(data)
        _logger.debug(f"已向流式任务 {task_id} 添加数据，大小: {len(data)} 字节")
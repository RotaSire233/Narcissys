import asyncio
import asyncudp
import traceback
from typing import Optional, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import redis

# 项目模块导入
from .configs import UdpConfigs
from .protocol import RequestType, DefaultProtocolHeader
from .cache import (
    StaticCache, StreamCache,
    StaticBufferStruct, StreamBufferStruct, FltStruct,
    AudStruct, ImgStruct
)
from .glob import PortPool
from loguru import logger

_logger = logger
r = redis.Redis()
#_data_logger = log.get_child_logger('data', enable_console=True)

# UDP 配置
LISTEN_IP = UdpConfigs.LISTEN_IP
LISTEN_PORT_RANGE = UdpConfigs.LISTEN_PORT_RANGE
BUFFER_SIZE = UdpConfigs.BUFFER_SIZE
MAX_WORKERS = UdpConfigs.MAX_WORKERS
QUEUE_SIZE = UdpConfigs.QUEUE_SIZE
PORT_CACHE = PortPool()
PORT_CACHE.register_range(*LISTEN_PORT_RANGE)


class UdpDriver(asyncio.Protocol):
    """基于 asyncudp 的异步 UDP 驱动器，支持静态/流式数据缓存处理"""
    thread_name = "UdpDriver"

    # 共享缓存
    

    def __init__(self,
                 ip: str = None,
                 port_range: PortPool = None,
                 header_cache=None,
                 buffer_size: int = None,
                 queue_size: int = None,
                 max_workers: int = None,
                 request=None):
        super().__init__()

        # 初始化配置
        self.ip = ip or LISTEN_IP
        self.buffer_size = buffer_size or BUFFER_SIZE
        self.queue_size = queue_size or QUEUE_SIZE
        self.max_workers = max_workers or MAX_WORKERS
        self.request = request or RequestType
        self.header_cache = header_cache or DefaultProtocolHeader()
        self.header_cache_len = len(self.header_cache)
        self.static_cache = StaticCache()
        self.stream_cache = StreamCache()
        
        self.running = True
        self.sock = None

        # 端口分配
        self.port_range = PORT_CACHE
        self.port = self.port_range.allocate_port()
        if not self.port:
            _logger.error("端口分配失败")
            raise RuntimeError("No available port")

        _logger.info(f"UDP 线程 {self.thread_name} 监听 {self.ip}:{self.port}")

        # 缓存系统初始化
        self.cache_map = {
            'static': StaticBufferStruct,
            'stream': StreamBufferStruct,
            'init': StreamBufferStruct,
        }
        _logger.info('数据缓存区注入UDP驱动完成')

        # 线程池
        self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._loop = asyncio.get_event_loop()

    async def listen(self):
        """启动 UDP 接收监听"""
        self.sock = await asyncudp.create_socket(local_addr=(self.ip, self.port))
        _logger.info(f"UDP Socket 启动成功，监听 {self.ip}:{self.port} {self.running}")
        
        while self.running:
            try:
                _logger.info(f"等待接收包")
                data, addr = await self.sock.recvfrom()
                _logger.info(f"接收数据包: {addr} ; 数据长度: {len(data)}")
                if len(data) < self.header_cache_len:
                    continue
                
                head = data[:self.header_cache_len]
                #_data_logger.debug(f"数据包头: {head}")
                payload = data[self.header_cache_len:]
                #_data_logger.debug(f"数据包体: {payload}")
                protocol_header = self.header_cache.decode_method(head)
                decode_func, decode_type = self.request.get_decoder(
                    channel=protocol_header.channel,
                    port=protocol_header.port,
                    decode=protocol_header.decode
                )

                decoded_data = await self._loop.run_in_executor(
                    self._executor,
                    decode_func,
                    payload
                )
                #_data_logger.debug(f"解码数据{decoded_data}")
                await self._add_to_cache(addr, decoded_data, decode_type)
                

            except Exception as e:
                _logger.error(f"\033[91m数据包解析错误:\033[0m")
                _logger.debug(f"\033[91m{traceback.format_exc()}\033[0m")

    async def _add_to_cache(self,
                           addr: Tuple[str, int],
                           decoded_data: Any,
                           decode_type: str):
        
        """处理缓存逻辑"""
        decoded_data["addr"] = addr

        cache = self.cache_map.get(decode_type, None)
        #_data_logger.debug(f"解码类型: {decode_type}")
        if cache is None:
            _logger.debug("缓存类型不存在")
            return

        try:
            if decode_type == "static":
                buffer = cache(id=decoded_data["id"],
                                  uid=decoded_data["uid"],
                                  name=decoded_data["name"],
                                  data=decoded_data["data"],
                                  timestamp=decoded_data["timestamp"],
                                  addr=addr,
                                  rout=decoded_data["rout"])
                _logger.info("静态数据缓冲赋值成功")
                self.static_cache.add(buffer=buffer)

            elif decode_type == "stream":
                buffer = self.stream_cache.get_by_id(id=decoded_data["uid"])
                buffer.datas.add_chunk(chunk=decoded_data["data"], 
                                        chunk_id=decoded_data["chunk"])
                _logger.info("流数据缓冲赋值成功")

            elif decode_type == "init":
                data_struct = cache(
                        id = decoded_data["id"],
                        uid = decoded_data["uid"],
                        name = decoded_data["name"],
                        timestamp = decoded_data["timestamp"],
                        addr = addr,
                        rout = decoded_data["rout"] + "/chunck",

                    )
                if decoded_data["type"] == "flt":
                    
                    buffer = FltStruct(id=decoded_data["id"],
                                       uid=decoded_data["uid"],
                                       name=decoded_data["name"],
                                       timestamp=decoded_data["timestamp"],
                                       stream_length=decoded_data["stream_len"],
                                       addr=addr,
                                       rout=decoded_data["rout"],
                                       datas=data_struct)
                    

                    self.stream_cache.init_stream(buffer=buffer)
                    _logger.info("flt数据缓冲赋值成功")

                elif decoded_data["type"] == "aud":
                    
                    buffer = AudStruct( id=decoded_data["id"],
                                         uid=decoded_data["uid"],
                                         name=decoded_data["name"],
                                         timestamp=decoded_data["timestamp"],
                                         formats=decoded_data["format"],
                                         sample_rate=decoded_data["sample_rate"],
                                         bit_depth=decoded_data["bit_depth"],
                                         channels=decoded_data["channels"],
                                         addr=addr,
                                         rout=decoded_data["rout"],
                                         datas=data_struct)
                    self.stream_cache.init_stream(buffer=buffer)
                    _logger.info("aud数据缓冲赋值成功")
                    

                elif decoded_data["type"] == "img":
                    buffer = ImgStruct(id=decoded_data["id"],
                                       uid=decoded_data["uid"],
                                       name=decoded_data["name"],
                                       timestamp=decoded_data["timestamp"],
                                       format=decoded_data["format"],
                                       size=decoded_data["size"],
                                       addr=addr,
                                       rout=decoded_data["rout"],
                                       datas=data_struct)
                    self.stream_cache.init_stream(buffer=buffer)
                    _logger.info("img数据缓冲赋值成功")


        except Exception as e:
            _logger.error(f"\033[91m缓冲区错误:\033[0m")
            _logger.error(f"\033[91m{traceback.format_exc()}\033[0m")

    async def run(self):
        """启动异步监听"""
        _logger.info("启动 UDP 驱动器")
        await self.listen()

    def stop(self):
        """安全停止驱动器"""
        self.running = False
        if self.sock:
            self.sock.close()
        self._executor.shutdown(wait=False)
        _logger.info("UDP 驱动器已关闭")
    

    
class UdpManager:
    """UDP服务管理器"""

    def __init__(self):
        self.drivers = {}
        self.tasks = {}
        self._lock = asyncio.Lock()
        self.cur_cache = None
        
    async def create_driver(self, **kwargs):

        """创建并启动一个新的UDP驱动器，自动生成ID"""
        async with self._lock:
            driver_id = f"udp_driver_{len(self.drivers) + 1}"
            while driver_id in self.drivers:
                driver_id = f"udp_driver_{len(self.drivers) + 1}_{asyncio.get_event_loop().time()}"
            
            driver = UdpDriver(**kwargs)
            self.drivers[driver_id] = driver
            
            task = asyncio.create_task(driver.run(), name=driver_id)
            self.tasks[driver_id] = task
            
            _logger.info(f"已创建UDP驱动器 {driver_id}，监听端口 {driver.port}")
            
            return driver_id, driver


    async def stop_driver(self, driver_id: str):
        """停止指定的UDP驱动器"""
        async with self._lock:
            if driver_id not in self.drivers:
                raise ValueError(f"UDP驱动器 {driver_id} 不存在")
            
            # 停止驱动器
            driver = self.drivers[driver_id]
            driver.stop()
            
            # 取消任务
            if driver_id in self.tasks:
                task = self.tasks[driver_id]
                if not task.done():
                    task.cancel()
            
            # 移除记录
            del self.drivers[driver_id]
            if driver_id in self.tasks:
                del self.tasks[driver_id]
            
            _logger.info(f"已停止UDP驱动器 {driver_id}")
    
    async def stop_all_drivers(self):
        """停止所有UDP驱动器"""
        async with self._lock:
            driver_ids = list(self.drivers.keys())
            for driver_id in driver_ids:
                try:
                    await self.stop_driver(driver_id)
                except Exception as e:
                    _logger.error(f"停止驱动器 {driver_id} 时出错: {e}")
    
    def get_driver_info(self, driver_id: str):
        """获取驱动器信息"""
        if driver_id not in self.drivers:
            return None
        
        driver = self.drivers[driver_id]
        task = self.tasks.get(driver_id)
        
        return {
            "driver_id": driver_id,
            "port": driver.port,
            "ip": driver.ip,
            "running": driver.running,
            "task_done": task.done() if task else None
        }

    def choose_driver_cache(self, driver_id: str):
        """获取指定驱动器的缓存数据"""
        if driver_id not in self.drivers:
            raise ValueError(f"UDP驱动器 {driver_id} 不存在")
        
        driver: UdpDriver = self.drivers[driver_id]
        self.cur_cache = {
            "static_cache": driver.static_cache,
            "stream_cache": driver.stream_cache
        }

    def list_drivers(self):
        """列出所有驱动器信息"""
        return [self.get_driver_info(driver_id) for driver_id in self.drivers.keys()]
    
    @property
    def static_cache(self) -> StaticCache:
        return self.cur_cache["static_cache"]
    
    @property
    def stream_cache(self) -> StreamCache:
        return self.cur_cache["stream_cache"]
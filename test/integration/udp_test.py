import socket
import random
import struct
from typing import Tuple
import asyncio
import pytest
from fastapi.testclient import TestClient
from loguru import logger as _logger

from core.core import app, udp_manager
import traceback


# 模拟发送的设备信息
DEVICE_ID = "01020304"
TIMESTAMP = 123456  # 模拟时间戳
UID_COUNTER = 1000  # UID 计数器，每次递增

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop

@pytest.fixture(scope="module")
async def udp_driver():
    response = client.post("/network/udp/drivers")
    assert response.status_code == 200 
    driver_info = response.json()

    driver_id = driver_info["driver_id"]
    response = client.get(f"/network/udp/drivers/choose/{driver_id}")
    assert response.status_code == 200

    yield driver_info


@pytest.fixture(scope="module")
def udp_driver_info(client):
    """创建UDP驱动器并返回其信息"""
    response = client.post("/network/udp/drivers")
    assert response.status_code == 200
    driver_info = response.json()
    
    driver_id = driver_info["driver_id"]
    response = client.get(f"/network/udp/drivers/choose/{driver_id}")
    assert response.status_code == 200
    
    yield driver_info

def build_protocol_header(channel: int, port: int, decode: int, length: int) -> bytes:
    """构建协议头"""
    buffer = bytearray()
    buffer.extend(struct.pack('>B', channel))   # channel: 1字节
    buffer.extend(struct.pack('>B', port))      # port: 1字节
    buffer.extend(struct.pack('>B', decode))    # decode: 1字节
    buffer.extend(struct.pack('>B', length))    # length: 1字节
    return bytes(buffer)

def build_float_init_packet(device_id: str = DEVICE_ID, timestamp: int = TIMESTAMP):
    """构造 float 初始化包"""
    # 先构建数据部分
    data_buffer = bytearray()
    data_buffer.extend(bytes.fromhex(device_id))
    data_buffer.extend(struct.pack('>Q', timestamp)[2:8])
    data_buffer.extend(struct.pack('>I', UID_COUNTER))
    data_buffer.extend(struct.pack('>i', 10))  # stream_length = 10
    
    # 构建完整包（协议头+数据）
    data_bytes = bytes(data_buffer)
    header = build_protocol_header(0x01, 0x00, 0x13, len(data_bytes))  # FLT_I类型
    return header + data_bytes

def build_fls_value_packet(device_id: str = DEVICE_ID, timestamp: int = TIMESTAMP):
    """构造 flow str (fls) 数据包"""
    # 先构建数据部分
    data_buffer = bytearray()
    data_buffer.extend(bytes.fromhex(device_id))
    data_buffer.extend(struct.pack('>Q', timestamp)[2:8])
    data_buffer.extend(struct.pack('>I', UID_COUNTER))

    # 生成随机字符串数据
    value = f"flow_data_{random.randint(0, 1000)}"
    data_buffer.extend(bytes([len(value)]))
    data_buffer.extend(value.encode('utf-8'))

    # 添加包索引
    packet_index = random.randint(0, 9)
    data_buffer.extend(struct.pack('>i', packet_index))
    
    # 构建完整包（协议头+数据）
    data_bytes = bytes(data_buffer)
    header = build_protocol_header(0x01, 0x01, 0x13, len(data_bytes))  # FLT类型
    return header + data_bytes

def build_audio_init_packet(device_id: str = DEVICE_ID, timestamp: int = TIMESTAMP):
    """构造 audio 初始化包"""
    # 先构建数据部分
    data_buffer = bytearray()
    data_buffer.extend(bytes.fromhex(device_id))
    data_buffer.extend(struct.pack('>Q', timestamp)[2:8])
    data_buffer.extend(struct.pack('>I', UID_COUNTER))
    # format: PCM
    data_buffer.extend(b'PCM')
    # sample rate
    data_buffer.extend(struct.pack('>i', 44100))
    # bit depth
    data_buffer.extend(bytes([16]))
    # channels
    data_buffer.extend(bytes([2]))
    
    # 构建完整包（协议头+数据）
    data_bytes = bytes(data_buffer)
    header = build_protocol_header(0x01, 0x00, 0x14, len(data_bytes))  # AUD_I类型
    return header + data_bytes

def build_image_init_packet(device_id: str = DEVICE_ID, timestamp: int = TIMESTAMP):
    """构造 image 初始化包"""
    # 先构建数据部分
    data_buffer = bytearray()
    data_buffer.extend(bytes.fromhex(device_id))
    data_buffer.extend(struct.pack('>Q', timestamp)[2:8])
    data_buffer.extend(struct.pack('>I', UID_COUNTER))
    # format: RGB888
    data_buffer.extend(b'888')
    # width, height
    data_buffer.extend(struct.pack('>H', 640))
    data_buffer.extend(struct.pack('>H', 480))
    
    # 构建完整包（协议头+数据）
    data_bytes = bytes(data_buffer)
    header = build_protocol_header(0x01, 0x00, 0x15, len(data_bytes))  # IMG_I类型
    return header + data_bytes

def send_udp_packet(sock: socket.socket, addr: Tuple[str, int], packet: bytes):
    """发送 UDP 数据包"""
    sock.sendto(packet, addr)
    _logger.info(f"[发送] 已发送 {len(packet)} 字节数据到 {addr}")


def test_udp_driver_integration(client, udp_driver_info):
    """测试UDP驱动器集成"""
    _logger.info("[测试] UDP驱动器集成测试开始")
    
    # 获取驱动器端口
    server_addr = ('127.0.0.1', udp_driver_info["port"])
    _logger.info(f"[测试] 连接到 {server_addr}")
    
    # 创建测试 socket
    test_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        # 等待确保驱动器完全启动
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(1))
        
        # 发送 float 初始化包
        _logger.info("[测试] 发送 float 初始化包")
        packet = build_float_init_packet()
        send_udp_packet(test_sock, server_addr, packet)
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.5))
        
        # 发送 flow str (fls) 数据包
        _logger.info("[测试] 发送 flow str 数据包")
        packet = build_fls_value_packet()
        send_udp_packet(test_sock, server_addr, packet)
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.5))
        
        # 发送 audio 初始化包
        _logger.info("[测试] 发送 audio 初始化包")
        packet = build_audio_init_packet()
        send_udp_packet(test_sock, server_addr, packet)
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.5))
        
        # 发送 image 初始化包
        _logger.info("[测试] 发送 image 初始化包")
        packet = build_image_init_packet()
        send_udp_packet(test_sock, server_addr, packet)
        asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.5))
        
        # 验证数据是否被正确接收和缓存
        response = client.get("/api/data/network/udp/cache/all")
        assert response.status_code == 200
        _logger.info(f"[测试] 缓存数据: {response.json()}")
        
    except Exception as e:
        _logger.info(f"[错误] 测试过程中发生错误: {e}")
        _logger.info(traceback.format_exc())
        raise
    finally:
        test_sock.close()
        _logger.info("[测试] 测试完成，关闭连接")




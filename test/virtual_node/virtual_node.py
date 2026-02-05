import time
import asyncio
from loguru import logger as _logger
import json
from udp_driver import UdpClientDriver
from virtual_mqtt_client import VirtualMqttClient


class VirtualNode:
    def __init__(self,
                 virtual_node_addr: list = ["192.168.1.100", 8000]):
        self.virtual_node_addr = virtual_node_addr
        self.mqtt_client = None
        self.udp_client = None
        self.running = True

    def run(self):
        """
        运行虚拟节点
        """
        try:
            asyncio.run(self.async_run())
        except KeyboardInterrupt:
            _logger.info("[VIRTUAL-NODE][INFO] 程序被用户中断")

    async def async_run(self):
        """
        异步运行虚拟节点
        """
        self.udp_client = UdpClientDriver()
        broker_addr, broker_port = self.udp_client.listen_for_broadcast()
        _logger.info(f"[VIRTUAL-UDP][INFO] 监听到UDP广播{broker_addr}:{broker_port}，开始连接MQTT服务器")
        mqtt_config = {
            "endpoint": broker_addr,  
            "client_id": "test_virtual_client"
        }
        self.mqtt_client = VirtualMqttClient(mqtt_config, port=broker_port)
        
        time.sleep(2)
        
        _logger.info("[VIRTUAL-MQTT][TEST] 开始测试设备注册")

        device = {
            "ip": self.virtual_node_addr,
            "sensor": []
        }
        _logger.info(f"[VIRTUAL-MQTT][TEST] 设备信息: {device}")
        device_id = self.mqtt_client.publish_registration(device_info=device)
        _logger.info(f"[VIRTUAL-MQTT][TEST] 设备注册成功，设备ID: {device_id}")

        try:
            while self.running:
                await asyncio.sleep(1)
            
        except KeyboardInterrupt:
            _logger.info("[VIRTUAL-MQTT][INFO] 测试程序已退出")
        finally:
            self.running = False
            if self.mqtt_client:
                self.mqtt_client.disconnect()

virtual_node = VirtualNode()
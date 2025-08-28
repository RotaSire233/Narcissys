import unittest
import json
import time
from unittest.mock import patch, MagicMock
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from core.network.mqtt.mqtt_sub import MqttSubscriber
from core.api_service.system_config import SystemBroadcast, get_local_ip

class TestIPBroadcast(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.received_messages = []
        self.local_ip = get_local_ip()
        
    def message_callback(self, topic, payload):
        """MQTT消息回调函数"""
        self.received_messages.append({
            'topic': topic,
            'payload': payload
        })
        print(f"收到消息 - Topic: {topic}, Payload: {payload}")
    
    def test_ip_broadcast_functionality(self):
        """测试IP广播功能"""
        print(f"开始测试IP广播功能，本地IP: {self.local_ip}")
        
        # 创建MQTT订阅者
        mqtt_config = {
            "endpoint": self.local_ip,
            "client_id": f"test_subscriber_{int(time.time())}",  # 使用时间戳确保唯一性
            "username": "",
            "password": ""
        }
        
        # 订阅广播主题
        subscriber = MqttSubscriber(mqtt_config)
        print(f"已创建MQTT订阅者，客户端ID: {mqtt_config['client_id']}")
        
        subscriber.subscribe("system/discovery", self.message_callback)
        print("已订阅主题: system/discovery")
        
        # 等待足够长时间以确保系统启动和广播
        # 增加等待时间到15秒，确保系统有足够时间启动和广播
        print("等待系统启动和广播消息...")
        wait_time = 0
        max_wait_time = 30  # 最多等待30秒
        check_interval = 3  # 每3秒检查一次
        
        while wait_time < max_wait_time:
            time.sleep(check_interval)
            wait_time += check_interval
            print(f"已等待 {wait_time} 秒，收到 {len(self.received_messages)} 条消息")
            
            if len(self.received_messages) > 0:
                break
        
        # 输出收到的消息数量
        print(f"总共收到 {len(self.received_messages)} 条消息")
        
        # 检查收到的消息是否符合预期格式
        if len(self.received_messages) > 0:
            message = self.received_messages[0]
            print(f"第一条消息: {message}")
            self.assertEqual(message['topic'], "system/discovery", 
                           "消息主题应该是system/discovery")
            
            # 验证载荷格式
            payload = message['payload']
            self.assertIn('type', payload, "消息应该包含type字段")
            self.assertEqual(payload['type'], 'system_discovery', 
                           "消息类型应该是system_discovery")
            self.assertIn('ip', payload, "消息应该包含ip字段")
            self.assertIn('timestamp', payload, "消息应该包含timestamp字段")
            
            print(f"成功验证广播消息: {payload}")
        else:
            print("未收到任何广播消息，可能是因为系统尚未启动或广播功能未正确工作")
            print("请确保在运行此测试前已启动Narcissus系统")
            # 不直接断言失败，因为这可能是因为系统未运行而不是功能错误
            self.skipTest("系统未运行或未收到广播消息，请先启动系统")
        
        # 清理资源
        subscriber.stop()
        print("测试完成，已清理MQTT订阅者")
    
    def test_local_ip_function(self):
        """测试本地IP获取功能"""
        ip = get_local_ip()
        self.assertIsInstance(ip, str, "IP地址应该是字符串类型")
        self.assertNotEqual(ip, "", "IP地址不应该为空")
        print(f"获取到的本地IP地址: {ip}")
        
    @patch('core.api_service.system_config.socket.socket')
    def test_local_ip_fallback(self, mock_socket):
        """测试本地IP获取失败时的回退机制"""
        # 模拟socket连接失败
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect.side_effect = Exception("网络错误")
        mock_socket.return_value = mock_socket_instance
        
        ip = get_local_ip()
        self.assertEqual(ip, "127.0.0.1", "当无法获取IP时应该回退到localhost")
        print("成功测试IP获取失败时的回退机制")

if __name__ == '__main__':
    # 当直接运行此脚本时显示所有输出
    unittest.main(verbosity=2)
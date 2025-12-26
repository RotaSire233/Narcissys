import socket
from dataclasses import dataclass
import os

def get_local_ip():
    """
    获取本机IP地址
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
    
LOCAL_IP = get_local_ip()
    
@dataclass(frozen=True)
class SystemBroadcast:
    SYSTEM_BROADCAST = {
        "endpoint": LOCAL_IP,
        "client_id": "system_ip",
        "username": "",
        "password": ""
    }
    BROADCAST = "syst/broadcast"

@dataclass(frozen=True)
class SystemInfo:
    SYSTEM_CONFIG = {
        "endpoint": LOCAL_IP,
        "client_id": "sensor_monitor",
        "username": "",
        "password": ""
    }
    REGIST = "syst/regist"
    UNREGIST = "syst/unregist"
import subprocess
import os
import sys
import time
from loguru import logger as _logger

def start_mosquitto(mos_path: str, config_path: str):
    
    if not os.path.exists(mos_path):
        _logger.error(f"[MQTT-BLOCK] 错误: 找不到mosquitto可执行文件: {mos_path}")
        return False, None
        
    if not os.path.exists(config_path):
        _logger.error(f"[MQTT-BLOCK] 错误: 找不到配置文件: {config_path}")
        return False, None
    
    try:
        process = subprocess.Popen(
            [mos_path, "-c", config_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        time.sleep(1)
        
        if process.poll() is None:
            _logger.info("[MQTT-BLOCK] Mosquitto MQTT Broker 已成功启动在后台运行")
            _logger.info("[MQTT-BLOCK] PID:", process.pid)
            return True, process.pid
        else:
            _logger.error("[MQTT-BLOCK] Mosquitto启动失败")
            stdout, stderr = process.communicate()
            _logger.error("错误输出:", stderr.decode('utf-8'))
            return False, None
            
    except Exception as e:
        _logger.error(f"[MQTT-BLOCK] 启动Mosquitto时发生错误: {e}")
        return False , None
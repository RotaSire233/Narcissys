
from dataclasses import dataclass
from ...net_manager import LOCAL_IP

@dataclass(frozen=True)
class Regist:
    SYSTEM_CONFIG = {
        "endpoint": LOCAL_IP,
        "client_id": "sensor_monitor",
        "username": "",
        "password": ""
    }
    REGIST = "syst/regist"
    UNREGIST = "syst/unregist"
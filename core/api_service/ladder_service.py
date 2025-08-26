from core.core import app
from fastapi import APIRouter
from typing import Dict
from loguru import logger as _logger
from .mqtt_server import cach as mqtt_cache
from core.ladder_backend import *

router = APIRouter(prefix="/api/ladder", tags=["ladder"])


ladder_command = LadderCommand()
@router.post("/components/ladder/add")
async def add_component(component: Dict):
    _logger.debug(f"收到：{component}")
    ladder_element = ElementClass(id=component["id"],
                                  bbox=component["bbox"],
                                  dtype=component["type"])
    valid = ladder_command.add_component(ladder_element)
    return {"valid": valid}

@router.post("/components/ladder/delete")
async def del_component(component: Dict):
    valid = ladder_command.del_component(component["id"])
    if valid is not None:
        return {"valid": valid}
    else:
        return {"valid": []}

@router.get("/components/ladder/sensor/get")
async def get_sensor():
    namespace = mqtt_cache.get_all_namespaces()
    return {"sensor": namespace}

@router.post("/components/ladder/sensor/add")
async def add_sensor(component: Dict):
    c_id = component["id"]
    sensor = component["sensor"]
    _logger.debug(f"收到：{sensor}")

app.include_router(router)
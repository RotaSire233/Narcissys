from core.core import app
from fastapi import APIRouter
from typing import Dict
from loguru import logger as _logger
from .mqtt_server import cach as mqtt_cache
from core.ladder_backend import *


router = APIRouter(prefix="/api/ladder", tags=["ladder"])


ladder_group = LadderGroup()
compiler = LadderCompile()
@router.post("/components/ladder/add")
async def add_component(component: Dict):
    _logger.debug(f"收到：{component}")
    ladder_element = ElementClass(id=component["id"],
                                  rung=component["rung_index"],
                                  bbox=component["bbox"],
                                  dtype=component["type"])
    command: LadderCommand = ladder_group.work_on_ladder(ladder_element.rung)

    valid = command.add_component(ladder_element)
    return {"valid": valid}

@router.post("/components/ladder/delete")
async def del_component(component: Dict):
    command: LadderCommand = ladder_group.work_on_ladder(component["rungIndex"])
    valid = command.del_component(component["id"])
    if valid is not None:
        return {"valid": valid}
    else:
        return {"valid": []}
    
@router.post("/components/ladder/compile")
async def compile_ladder(infos: Dict):
    _logger.info(f"Compiling ladder gets: {infos}")
    compiled = compiler(ladder_group, infos)
    _logger.info(f"Compile Result: {compiled}")
    if compiled["success"]:
        data_process = process(compiler)
        if data_process:
            return {"success": True}
    else:
        return {"success": False, "error": "error(Error Engine Will Be Added In Future)"}


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
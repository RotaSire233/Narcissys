from fastapi import APIRouter, BackgroundTasks, Body
from core.core import app
from typing import Dict, Any, List, Optional
from loguru import logger as _logger
import uuid
from pydantic import BaseModel

from core.model_api import *

router = APIRouter(prefix="/api/model", tags=["model"])
api_keys = ApiKeys()
onnx_api = OnnxApi()

llm_Driver : ClientBase = None

# ONNX 模型表
onnx_list = model_cage
stream_tasks = {}

class StreamRequest(BaseModel):
    prompt: List[Dict[str, str]]
    model: Optional[str] = None
    system_prompt: Optional[str] = None

@router.get("/api_keys/info")
async def api_keys_info():
    return api_keys.keys_json
@router.post("/api_keys/update")
async def update_api_keys(update_info: Dict):
    api_name, api_key = update_info["api_name"], update_info["api_key"]
    api_keys.update_api_key(api_name, api_key)
    _logger.info(f"update api key: {api_name}")
    return {"code": "200"}


@router.post("/onnxapi/add")
async def add_model(model_name: str, 
                    model_info: InitStruct):
    model_cage.add_model(model_name, model_info)
    return {"message": "/onnxapi/add"}

@router.post("/onnxapi/delete")
async def delete_model(model_name: str):
    model_cage.del_model(model_name)
    return {"message": "/onnxapi/remove"}


@router.post("/onnxapi/run")
async def run_model(model_name: str):
    onnx_api.add_model(model_name)
    return {"message": "/onnxapi/run"}

@router.post("/onnxapi/stop")
async def stop_model(model_name: str):
    onnx_api.remove_model(model_name)
    return {"message": "/onnxapi/stop"}

@router.post("/onnxapi/inference")
async def inference(model_name: str, input_data: Dict[str, list]) -> ResponseStruct:
    np_input_data = {k: np.array(v) for k, v in input_data.items()}
    
    request_id = str(uuid.uuid4())
    request = RequestStruct(model_name, 
                            np_input_data, 
                            request_id)
    
    return onnx_api.inference(request)

@router.get("/onnxapi/info")
async def get_model_info(model_name: str) -> Optional[Dict[str, Any]]:
    return onnx_api.get_model_info(model_name)

app.include_router(router)
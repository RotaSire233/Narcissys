from fastapi import APIRouter, BackgroundTasks
from typing import Dict, Tuple, List, Optional
from loguru import logger as _logger
import uuid
from pydantic import BaseModel

from core.model_api import *

router = APIRouter(prefix="/api/model", tags=["model"])
api_keys = ApiKeys()
onnx_api = OnnxApi()

# LLM 模型表
llm_config : ApiConfig = None
llm_Driver : ClientBase = None

# ONNX 模型表
onnx_list = model_cage
stream_tasks = {}

class StreamRequest(BaseModel):
    prompt: List[Dict[str, str]]
    model: Optional[str] = None
    system_prompt: Optional[str] = None
@router.get("/api_keys/get")
async def get_api_keys():
    info = api_keys.info
    all_keys = {}
    key: str
    value: KeyView
    for key, value in info.items():
        all_keys[key] = {"key": value.key,
                         "url": value.url,
                         }
    return all_keys

@router.post("/api_keys/update")
async def update_api_keys(api_name: str, api_key: str):
    api_keys.update_api_key(api_name, api_key)
    return {"code": "200"}

@router.get("/api_keys/support")
async def support_api_keys():
    support_list = SupportList()
    return support_list.__dict__

@router.get("/api_keys/info")
async def api_keys_info():
    return api_keys.keys_json

@router.post("/api_keys/choose")
async def choose_api_keys(api_name: str):
    global llm_config
    info = api_keys.info.get(api_name, None)
    llm_config = ApiConfig(api_keys=info.key, base_url=info.url)
    return {"code": "200"}

@router.post("/llmapi/init")
async def init_llmapi():
    global llm_api
    if llm_config is not None:
        llm_api = ClientBase(llm_config)

        return {"code": "200"}
    else:
        return {"code": "500"}
    
async def process_stream_task(task_id: str, request: StreamRequest):
    """
    处理流式请求的后台任务
    """
    try:
        if request.model:
            llm_Driver.set_model(request.model)
        
        if request.system_prompt:
            llm_Driver.set_system_prompt(request.system_prompt)
        
        llm_Driver.stream = True
        
        result_chunks = []
        async for chunk in llm_Driver.chat_stream(request.prompt):
            result_chunks.append(chunk)
            stream_tasks[task_id]["status"] = "processing"
            stream_tasks[task_id]["chunks"] = result_chunks
        
        # 标记任务完成
        stream_tasks[task_id]["status"] = "completed"
        stream_tasks[task_id]["result"] = "".join(result_chunks)
        
    except Exception as e:
        stream_tasks[task_id]["status"] = "failed"
        stream_tasks[task_id]["error"] = str(e)
        _logger.error(f"流式任务 {task_id} 处理失败: {e}")

@router.post("/llmapi/stream")
async def llmapi_stream(request: StreamRequest, background_tasks: BackgroundTasks):
    """
    流式LLM API接口
    """
    task_id = str(uuid.uuid4())
    
    # 初始化任务状态
    stream_tasks[task_id] = {
        "status": "pending",
        "chunks": [],
        "result": None,
        "error": None
    }
    
    # 在后台处理流式请求
    background_tasks.add_task(process_stream_task, task_id, request)
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": f"/llmapi/stream/{task_id}"
    }

@router.get("/llmapi/stream/get/{task_id}")
async def get_stream_result(task_id: str):
    """
    根据任务ID获取流式处理结果
    """
    if task_id not in stream_tasks:
        return {"error": "No task found."}
    
    task_info = stream_tasks[task_id]
    
    return {
        "task_id": task_id,
        "status": task_info["status"],
        "chunks": task_info["chunks"],
        "result": task_info["result"],
        "error": task_info["error"]
    }

@router.delete("/llmapi/stream/delete/{task_id}")
async def delete_stream_result(task_id: str):
    """
    删除任务结果以释放内存
    """
    if task_id in stream_tasks:
        del stream_tasks[task_id]
        return {"message": "/llmapi/stream/{task_id}/delete"}
    else:
        return {"error": "No task found."}
    
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
async def inference(model_name: str, input_data: Dict[str, np.ndarray]) -> ResponseStruct:

    request_id = str(uuid.uuid4())
    request = RequestStruct(model_name, 
                            input_data, 
                            request_id)
    
    return onnx_api.inference(request)

@router.get("/onnxapi/info")
async def get_model_info(model_name: str) -> Optional[Dict[str, Any]]:
    return onnx_api.get_model_info(model_name)
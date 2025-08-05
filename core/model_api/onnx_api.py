import onnxruntime as rt
from typing import (Union, List, Final, 
                    Optional, Dict, Any,
                    TypedDict, Tuple)
import time
import numpy as np
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
"""
------------------------------------------------------------------------
# numpy < 2.0.0 2.0.0以上版本兼容老模型一堆问题在这个onnx兼容问题官方解决之前
暂时维持在numpy2.0.0版本以下，如果onnx模型更新，请自行更新numpy版本
------------------------------------------------------------------------
"""
class InitStruct(TypedDict):
    """初始化结构"""
    model_path: str
    model_info: Union[Dict[str, Any], None]
    use_gpu: bool
    time_out: int

class RequestStruct:
    """请求结构"""
    def __init__(self,
                 model_name: str,
                 input_data: Dict[str, np.ndarray],
                 request_id: Optional[str] = None,
                 ):
        self.model_name = model_name   
        self.input_data = input_data
        self.request_id = request_id
        self.timestamp = time.time()

class ResponseStruct:
    """响应结构"""
    def __init__(self, 
                 success: bool,
                 result: Optional[Dict[str, Any]]=None,
                 request_id: Optional[str]=None,
                 error: Optional[str]=None,
                 latency: Optional[float]=None,
                ):
        self.success = success
        self.result = result
        self.error = error
        self.request_id = request_id
        self.latency = latency

class ModelDriver:
    """模型实例"""
    def __init__(self, config: InitStruct):
        self.config = config
        self.session = self._initialize_session()
        self._warmup()
        self.stats = {
            "total_requests": 0,
            "success_requests": 0,
            "last_active": time.time()
        }
    
    def _initialize_session(self) -> rt.InferenceSession:
        providers = ['CUDAExecutionProvider'] if self.config['use_gpu'] else ['CPUExecutionProvider']
        session_options = rt.SessionOptions()
        session_options.intra_op_num_threads = 1
        session_options.inter_op_num_threads = 1
        return rt.InferenceSession(
            self.config['model_path'],
            providers=providers,
            sess_options=session_options
        )

    def _warmup(self):
        try:
            dummy_inputs = {}
            for input_info in self.session.get_inputs():
                new_shape = []
                for dim in input_info.shape:
                    if isinstance(dim, str):  # 动态维度标记
                        new_shape.append(1)
                    elif dim is None:
                        new_shape.append(1)
                    else:
                        new_shape.append(1 if dim <= 0 else int(dim))
                
                dtype = self._map_numpy_type(input_info.type)
                dummy_inputs[input_info.name] = np.zeros(new_shape, dtype=dtype)
            
            start_time = time.time()
            self.session.run(None, dummy_inputs)

            # GPU需要额外预热一次
            if self.config['use_gpu']:
                self.session.run(None, dummy_inputs)
            
            warmup_time = (time.time() - start_time) * 1000
            print(f"Model Pre-heating done: {self.config['model_path']}, costs: {warmup_time:.2f}ms")

        except Exception as e:
            print(f"Pre-heating error: {e}")
    
    def _map_numpy_type(self, onnx_type: str) -> type:
        type_mapping = {
            'tensor(float)': np.float32,
            'tensor(int64)': np.int64,
            'tensor(int32)': np.int32,
            'tensor(bool)': np.bool_,
            'tensor(string)': np.str_,
            'tensor(float16)': np.float16,
            'tensor(double)': np.float64,
            'tensor(uint8)': np.uint8,
        }
        return type_mapping.get(onnx_type.split('(')[0], np.float32)
    
    def execute(self, request: RequestStruct) -> ResponseStruct:
        start_time = time.time()
        self.stats['total_requests'] += 1

        try: 
            outputs = self.session.run(None, request.input_data)
            output_names = [output.name for output in self.session.get_outputs()]
            result_dict = {name: data for name, data in zip(output_names, outputs)}
            
            self.stats["success_requests"] += 1
            self.stats["last_active"] = time.time()
            
            latency = (time.time() - start_time) * 1000
            return ResponseStruct(
                success=True,
                result=result_dict,
                request_id=request.request_id,
                latency=latency
            )
            
        except rt.OrtInvalidArgument as e:
            # 特定错误处理
            latency = (time.time() - start_time) * 1000
            return ResponseStruct(
                success=False,
                error=f"Input error: {str(e)}",
                request_id=request.request_id,
                latency=latency
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ResponseStruct(
                success=False,
                error=f"Inference error: {str(e)}",
                request_id=request.request_id,
                latency=latency
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            "config": dict(self.config),
            "inputs": [{
                "name": i.name, 
                "type": i.type, 
                "shape": i.shape
            } for i in self.session.get_inputs()],
            "outputs": [{
                "name": o.name, 
                "type": o.type, 
                "shape": o.shape
            } for o in self.session.get_outputs()],
            "stats": dict(self.stats)
        }

class OnnxApi:
    def __init__(self, max_workers=8):
        self.models: Dict[str, ModelDriver] = {}
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.request_counter = 0

    def add_model(self, 
                  model_name: str, 
                  config: InitStruct) -> Tuple[bool, str]:
        """添加模型"""
        with self.lock:
            if model_name in self.models:
                return False, f"Model {model_name} has been exist"
            try:
                instance = ModelDriver(config)
                self.models[model_name] = instance
                return True, f"Model {model_name} added successfully"

            except Exception as e:
                return False, f"Model load failure: {str(e)}"
    
    def remove_model(self, model_name: str) -> Tuple[bool, str]:
        """移除模型"""
        with self.lock:
            if model_name not in self.models:
                return False, f"Model {model_name} does not exist"
            del self.models[model_name]
            return True, f"Modle {model_name} has been removed"
    
    def model_exists(self, model_name: str) -> bool:
        """检查模型是否存在"""
        with self.lock:
            return model_name in self.models

    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取模型信息"""
        with self.lock:
            instance = self.models.get(model_name)
            return instance.get_model_info() if instance else None
        
    def list_models(self) -> List[str]:
        """获取所有模型名称"""
        with self.lock:
            return list(self.models.keys())
    
    def inference(self, request: RequestStruct) -> ResponseStruct:
        """执行推理请求"""
        # 检查模型是否存在
        if not self.model_exists(request.model_name):
            return ResponseStruct(
                success=False,
                error=f"Model '{request.model_name}' has not been added yet.",
                request_id=request.request_id
            )
        
        # 快速获取模型实例引用
        with self.lock:
            model_instance = self.models.get(request.model_name)
        
        if not model_instance:
            return ResponseStruct(
                success=False,
                error=f"Model class has not been initialized.",
                request_id=request.request_id
            )
        
        # 提交到线程池执行
        future = self.executor.submit(model_instance.execute, request)
        
        try:
            
            timeout_sec = model_instance.config.get('time_out', 5000) / 1000.0
            return future.result(timeout=timeout_sec)
        except TimeoutError:
            return ResponseStruct(
                success=False,
                error="Inference Error",
                request_id=request.request_id,
                latency=model_instance.config.get('time_out', 5000)
            )
        except Exception as e:
            return ResponseStruct(
                success=False,
                error=f"System error: {str(e)}",
                request_id=request.request_id
            )
    
    def shutdown(self):
        """关闭服务"""
        self.executor.shutdown()
        print("ONNX Server Shutdown")

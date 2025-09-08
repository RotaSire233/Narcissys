from typing import List, Dict, Tuple
from dataclasses import dataclass
import copy
from .ladder_backend import LadderCommand, LadderGroup, LadderComponents, ElementClass
from core.global_cache import global_cache, global_uid
from core.model_api.llm_api import *
from threading import Thread

keys = ApiKeys()
client_group = ClientGroup()

@dataclass
class ExistInfo:
    top: bool
    buttom: bool
    left: bool
    right: bool

class LadderCompile:
    def __init__(self):
        self.compiling = False
        self.registed_components = None

    def __call__(self, ladder_group: LadderGroup, connect_info: Dict):
        self.registed_components = {}
        self.input_device = set()
        self.output_device = []

        # 创建ladder_group的深拷贝副本
        ladder_group_copy = copy.deepcopy(ladder_group)
        
        compile_queue: List[LadderCommand] = ladder_group_copy.get_compile_queue
        for idx, ladder_rung in enumerate(compile_queue):
            legal, debug_info = self._structure_compile(ladder_rung)
            if not legal:
                return {"success": False, "debug_info": debug_info, "error_location": idx}


        info_queue = []
        
        for rung_idx in sorted(connect_info.keys()):
            info_queue.append(connect_info[rung_idx])

        for idx, rung in enumerate(info_queue):
            legal, debug_info = self._info_compile(info_queue[idx], compile_queue[idx])
            if not legal:
                return {"success": False, "debug_info": debug_info, "error_location": idx}
        return {"success": True, "compiled_group": ladder_group_copy}

    def _structure_compile(self, ladder_rung: LadderCommand):
        ladder_info = ladder_rung.components_dict
        ladder_pos = ladder_rung.components_location

        for i, ladder_row in enumerate(ladder_pos):
            ladder_size = (len(ladder_pos), len(ladder_row))
            for j, ladder_col in enumerate(ladder_row):
                idx = (i, j)
                component_info = ladder_info[ladder_col]
                legal, debug_info = self._connect_rules(idx, 
                                                        component_info, 
                                                        ladder_size, 
                                                        ladder_info, 
                                                        ladder_pos)
                if not legal:
                    return False, debug_info
        return True, ""
    def _info_compile(self, connect_info: List, ladder_rung: LadderCommand):
        info_output = ''
        ladder_info = ladder_rung.components_dict
        for info in connect_info:
            component_id = info["id"]
            component = ladder_info[component_id]
            name = info["name"]
            if name != "":
                if name in self.registed_components:
                    return False, "[NAME]: 名称重复"
                self.registed_components[name] = component_id
            dtype = component.dtype
            if dtype == LadderComponents.NORMAL_OPEN or dtype == LadderComponents.NORMAL_CLOSED:
                component.sensor.append(info['properties']['option'])
                self.input_device.add(info['properties']['option'])
               
                if info['properties']['option'] == "":
                    if name == "":
                        return False, f"[DEVICE]: 触点{component_id}未定义"
                    else:
                        return False, f"[DEVICE]: 触点{name}未定义"
                    
            elif dtype == LadderComponents.MODEL:
                component.model_mode = info['properties']['modelMode']
                component.model_name = info['properties']['modelName']
                component.model_params = info['properties']['modelParams']
                stream = info['properties']['stream']
                if stream == "true":
                    component.stream = True
                else:
                    component.stream = False
                if (info['properties']['modelMode'] == "" 
                    or info['properties']['modelName'] == "" 
                    or info['properties']['modelParams'] == ""
                    or info['properties']['stream'] == ""):
                    if name == "":
                        return False, f"[DEVICE]: 模型{component_id}未定义"
                    else:
                        return False, f"[DEVICE]: 模型{name}未定义"
                
            elif dtype == LadderComponents.COIL:
                component.device.append(info['properties']['option'])
                self.output_device.append(info['properties']['option'])
                if info['properties']['option']:
                    if name == "":
                       info_output = f"[DEVICE]: 线圈{component_id}忽视输出对象，api将直接输出数据"
                    else:
                       info_output = f"[DEVICE]: 线圈{name}忽视输出对象，api将直接输出数据"
        return True, info_output
    def _connect_rules(self,
                       idx: Tuple[int, int],
                       component: ElementClass,
                       ladder_size: Tuple[int, int],
                       ladder_info: List,
                       ladder_pos: List):
        
        exist_info = self._element_exist(ladder_size, idx)
        
        
        if component.dtype == LadderComponents.CONNECT_UP:
            if not exist_info.top:
                return False, "[CONNECT_UP]: 上方不存在元素"
            if not exist_info.left:
                return False, "[CONNECT_UP]: 左方不存在元素"
            prev_id = ladder_pos[idx[0]][idx[1] - 1]
            next_id = ladder_pos[idx[0] - 1][idx[1]]
            component.prev.append(ladder_info[prev_id])
            component.next.append(ladder_info[next_id])

        elif component.dtype == LadderComponents.CONNECT_DOWN:
            if not exist_info.buttom:
                return False, "[CONNECT_DOWN]: 下方不存在元素"
            if not exist_info.right:
                return False, "[CONNECT_DOWN]: 右方不存在元素"
            if not exist_info.left:
                return False, "[CONNECT_DOWN]: 左方不存在元素"
            prev_id = ladder_pos[idx[0]][idx[1] - 1]
            next_id_down = ladder_pos[idx[0] + 1][idx[1]]
            next_id_right = ladder_pos[idx[0]][idx[1] + 1]
            component.prev.append(ladder_info[prev_id])
            component.next.append(ladder_info[next_id_down])
            component.next.append(ladder_info[next_id_right])

        elif component.dtype == LadderComponents.COIL:
            if not exist_info.left:
                return False, "[COIL]: 左方不存在元素"
            if exist_info.right:
                return False, "[COIL]: 右方存在元素"
            prev_id = ladder_pos[idx[0]][idx[1] - 1]
            component.prev.append(ladder_info[prev_id])

        elif (component.dtype == LadderComponents.NORMAL_OPEN or
              component.dtype == LadderComponents.NORMAL_CLOSED or 
              component.dtype == LadderComponents.MODEL):
            if exist_info.left:
                prev_id = ladder_pos[idx[0]][idx[1] - 1]
                component.prev.append(ladder_info[prev_id])
            if not exist_info.right:
                return False, "[NORMAL_OPEN/NORMAL_CLOSED]: 右方不存在元素/线圈"
            
            next_id = ladder_pos[idx[0]][idx[1] + 1]
            component.next.append(ladder_info[next_id])

        elif component.dtype == LadderComponents.CONNECT_RIGHT:
            if not exist_info.right:
                return False, "[CONNECT_RIGHT]: 右方不存在元素"
            if not exist_info.top:
                return False, "[CONNECT_RIGHT]: 上方不存在元素"
            if exist_info.buttom:
                return False, "[CONNECT_RIGHT]: 下方存在元素"
            if exist_info.left:
                return False, "[CONNECT_RIGHT]: 左方存在元素"
            prev_id = ladder_pos[idx[0] - 1][idx[1]]
            next_id = ladder_pos[idx[0]][idx[1] + 1]
            component.prev.append(ladder_info[prev_id])
            component.next.append(ladder_info[next_id])
        return True, ""

    def _element_exist(self, ladder_size: Tuple[int, int], idx: Tuple[int, int]) -> ExistInfo:
        col_max = ladder_size[0]
        row_max = ladder_size[1]
        col_cur = idx[0]
        row_cur = idx[1]
        
        top = True
        buttom = True
        left = True
        right = True

        if col_cur == 0:
            top = False

        if col_cur == col_max - 1:
            buttom = False

        if row_cur == 0:
            left = False

        if row_cur == row_max - 1:
            right = False

        exist_info = ExistInfo(top, buttom, left, right)
        return exist_info
    

class Run_Complie(Thread):
    def __init__(self, compile_info: LadderGroup):
        from .data_compile import data_location
        super().__init__()
        self.info = compile_info
        self.compile_queue = compile_info.get_compile_queue()
        self.scan_loop_ms = None
        self.run_time = True
        self.data_location = data_location
        self.daemon = True  # 设置为守护线程

    def run(self):
        import time
        if self.scan_loop_ms is None:
            raise ValueError("scan_loop_ms must be set before starting the thread")
        
        while self.run_time:
            for rung in self.compile_queue:
                self._rung_process(rung)
            time.sleep(self.scan_loop_ms / 1000)
    
    def process(self, scan_ms):
        self.scan_loop_ms = scan_ms
        self.start()  # 启动线程

    def stop(self):
        self.run_time = False
    
    def _rung_process(self, ladder_rung: LadderCommand):
        graph_structure = ladder_rung.components_location
        graph_info = ladder_rung.components_dict
        max_cols = max(len(row) for row in graph_structure)
        for i in range(max_cols):
            cur_col_ele = []
            for row in graph_structure:
                if i < len(row):
                    cur_col_ele.append(row[i])
                else:
                    cur_col_ele.append(None)

        for j in range(max_cols):
            for i in range(len(graph_structure)):
                    element = graph_structure[i][j]
                    if element is not None:
                        self._element_process(element)

                    else:
                        continue

    def _element_process(self, element: ElementClass):
        if element.dtype == LadderComponents.NORMAL_OPEN:
            self._normal_open_process(element)
        elif element.dtype == LadderComponents.NORMAL_CLOSED:
            self._normal_close_process(element)
        elif element.dtype == LadderComponents.COIL:
            self._coil_process(element)
        elif element.dtype == LadderComponents.CONNECT_UP:
            self._connect_up_down_right_process(element)
        elif element.dtype == LadderComponents.CONNECT_DOWN:
            self._connect_up_down_right_process(element)
        elif element.dtype == LadderComponents.CONNECT_RIGHT:
            self._connect_up_down_right_process(element)
        elif element.dtype == LadderComponents.MODEL:
            self._model_process(element)

    def _load_from_prev(self, prev: ElementClass, current: ElementClass):
        for prev_element in prev:
            prev_element: ElementClass
            if prev_element is not None:
                if prev_element.done:
                    prev_sensor = prev_element.cur_data
                    for s in prev_sensor:
                        current.cur_data.append(s)

    def _normal_open_process(self, element: ElementClass):
        prev: List[ElementClass] = element.prev

        for s in element.sensor:
            element.cur_data.append(s)
            if global_cache.get_cache_condition(s):
                # 探针获取当前数据情况，如果存活，就直接定义为通路
                element.done = True
            else:
                element.done = False
                return 
            
        self._load_from_prev(prev, element)

    def _normal_close_process(self, element: ElementClass):
        prev: List[ElementClass] = element.prev

        for s in element.sensor:
            element.cur_data.append(s)
            if global_cache.get_cache_condition(s):
                # 探针获取当前数据情况，如果存活，就直接定义为通路
                element.done = False
            else:
                element.done = True
                return 
            
        self._load_from_prev(prev, element)

    def _coil_process(self, element: ElementClass) -> None:
        prev: List[ElementClass] = element.prev
        self._load_from_prev(prev, element)
        # coil api 逻辑现在不写

    def _connect_up_down_right_process(self, element: ElementClass) -> None:
        prev: List[ElementClass] = element.prev
        element.done = True
        self._load_from_prev(prev, element)

    def _model_process(self, element: ElementClass):
        prev: List[ElementClass] = element.prev
        self._load_from_prev(prev, element)
        if element.model_mode == "llm":
            if element.task_id == []:
                model_name = element.model_name
                api_info: KeyView = keys.get_api_info(model_name)
                llm_config = ApiConfig(api_info.key, api_info.url)
                llm_client = ClientBase(llm_config)
                client_group.regist_task(llm_client)
                if element.stream:
                    pass
                else:
                    llm_client.chat_completion(element)
            else:
                for td in element.task_id:
                    task = client_group.clients[td]
                    if task.done and not element.stream:
                        result = client_group.clients.pop(td).message
                        payload = {"id": element.id, "result": result}
                        element.cur_data.append(payload)
                    elif task.done and element.stream:
                        pass
        elif element.model_mode == "common":
            pass
                
       
            

        


            
    
    

            
            


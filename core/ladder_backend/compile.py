from loguru import logger as log
import json
import threading
from .ladder import RungCommand, LadderComponents,LadderGroup, ElementClass
from typing import Dict,Tuple,List
from dataclasses import dataclass

@dataclass
class ExistInfo:
    top: bool
    buttom: bool
    left: bool
    right: bool

class GroupCompiler:
    pass

class ProjectCompiler:
    def __init__(self):
        self.name_id = {} # 名称映射
        self.device_tabel = {}
        self.output_device = []

    def compile(self, path: str):
        with open(path, 'r', encoding='utf-8') as f:
            self.loaded_data = json.load(f)
        self.ladder_group = LadderGroup()
        for component in self.loaded_data.items():
            ladder_element = ElementClass(id=component["id"],
                                          rung=component["rung_index"],
                                          bbox=component["bbox"],
                                          dtype=component["type"],
                                          property=component["properties"],
                                          name=component["name"])
            command: RungCommand = self.ladder_group.work_on_ladder(ladder_element.rung)
            vaild = command.add_component(ladder_element)
            if not vaild:
                log.error(f"[ProjectCompiler]Add component {ladder_element.id} to rung {ladder_element.rung} failed")
        queue = self.ladder_group.get_compile_queue()
        self.compile_queue = []
        for idx, ladder_rung in enumerate(queue):
            legal, debug_info = self._compile_structure(ladder_rung)
            
            if not legal:
                return {"success": False, "debug_info": debug_info, "error_location": idx}

            legal, debug_info = self._compile_info(ladder_rung)

            if not legal:
                return {"success": False, "debug_info": debug_info, "error_location": idx}
        return {"success": True, "compile_queue": self.compile_queue}
    

    
    def _compile_structure(self,ladder_rung: RungCommand):
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
    
    def _compile_info(self, ladder_rung: RungCommand):
        ladder_info = ladder_rung.components_dict
        location_list = ladder_rung.components_location
        component: ElementClass
        for i, row in enumerate(location_list):
            for j,component_id in enumerate(row):
                component = ladder_info[component_id]
                self._compile_component(component,
                                        )
    def _compile_component(self, 
                           component: ElementClass):
        name = component.name
        if name in self.name_id:
            return False, f"[COMPILE][ELEMENT]: 名称{name}已存在"
        self.name_id[name] = component.id
        propertys = component.property
        dtype = component.dtype
        if dtype == LadderComponents.NORMAL_OPEN or dtype == LadderComponents.NORMAL_CLOSED:
            component.sensor = propertys["option"]
            self.device_tabel[propertys["option"]] = None
            if propertys["option"] == "":
                if name == "":
                    return False, f"[COMPILE][ELEMENT]: 触点{component.id}未定义"
                else:
                    return False, f"[COMPILE][ELEMENT]: 触点{name}未定义"
            
            elif dtype == LadderComponents.MODEL:
                component.model_mode = propertys['modelMode']
                component.model_name = propertys['modelName']
                component.model_params = propertys['modelParams']
                stream = propertys['stream']
                if stream == "true":
                    component.stream = True
                else:
                    component.stream = False
                if (component.model_mode == "" 
                    or component.model_name == "" 
                    or component.model_params == ""
                    or stream == ""):
                    if name == "":
                        return False, f"[COMPILE][ELEMENT]: 模型{component.id}未定义"
                    else:
                        return False, f"[COMPILE][ELEMENT]: 模型{name}未定义"
                    
            elif dtype == LadderComponents.COIL:
                    component.device.append(propertys['option'])
                    self.output_device.append(propertys['option'])
                    if propertys['option']:
                        if name == "":
                            info_output = f"[COMPILE][ELEMENT]: 线圈{component.id}忽视输出对象，api将直接输出数据"
                        else:
                            info_output = f"[COMPILE][ELEMENT]: 线圈{name}忽视输出对象，api将直接输出数据"

            return True, info_output
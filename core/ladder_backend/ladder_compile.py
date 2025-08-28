from .ladder_backend import LadderCommand, LadderGroup, LadderComponents, ElementClass
from typing import List, Dict, Tuple
from dataclasses import dataclass

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
        self.input_device = []
        self.output_device = []

        compile_queue: List[LadderCommand] = ladder_group.get_compile_queue()
        cur_compile_queue = compile_queue.copy()
        # 创建副本防止软编译冲突
        for idx, ladder_rung in enumerate(cur_compile_queue):
            legal, debug_info = self._structure_compile(ladder_rung)
            if not legal:
                return {"success": False, "debug_info": debug_info, "error_location": idx}


        info_queue = []
        for rung in sorted(connect_info.keys()):
            info_queue.append(connect_info[rung])
        for idx, rung in enumerate(info_queue):
            legal, debug_info = self._info_compile(info_queue[idx], ladder_rung)
            if not legal:
                return {"success": False, "debug_info": debug_info, "error_location": idx}
        return {"success": True}

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
                self.input_device.append(info['properties']['option'])
                if component.sensor == "":
                    if name == "":
                        return False, f"[DEVICE]: 触点{component_id}未定义"
                    else:
                        return False, f"[DEVICE]: 触点{name}未定义"
                
            elif dtype == LadderComponents.COIL:
                component.device.append(info['properties']['option'])
                self.output_device.append(info['properties']['option'])
                if component.device == "":
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

        elif component.dtype == LadderComponents.NORMAL_OPEN or component.dtype == LadderComponents.NORMAL_CLOSED:
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

from loguru import logger as _logger
from dataclasses import dataclass
from typing import Dict, Tuple, List
import json

@dataclass(frozen=True)
class LadderComponents:
    NORMAL_OPEN = 'normal_open'
    NORMAL_CLOSED = 'normal_closed'
    COIL = 'coil'
    MODEL = 'model'
    CONNECT_UP = 'connect_up'
    CONNECT_DOWN = 'connect_down'
    CONNECT_RIGHT = 'connect_right'

@dataclass
class ModelType:
    api = "api"
    llm = "llm"

class ElementClass:
    def __init__(self, id, bbox, dtype, name, rung ,done=False):
        self.id = id
        self.bbox = bbox
        self.dtype = dtype
        self.name = name
        self.rung = rung
        self.property = {}
        self.done = done
        self.available = False
        self.passed = False
        self.legal = True
        
        if dtype == LadderComponents.NORMAL_OPEN or dtype == LadderComponents.NORMAL_CLOSED:
            self.sensor = [] # {sensor_id: data_type}
        elif dtype == LadderComponents.COIL:
            self.device = [] # {device_id: data_type} 上位机-下位机尽可能交付
        elif dtype == LadderComponents.CONNECT_UP or dtype == LadderComponents.CONNECT_DOWN:
            self.target = None
        elif dtype == LadderComponents.MODEL:
            self.client = None
            self.sensor = []
            self.model_mode = None
            self.model_name = None
            self.model_params = None
            self.stream = False
            self.task_id = []
            
        self.prev: List['ElementClass'] = []
        self.next: List['ElementClass'] = []
        
        self.cur_data = []

class RungCommand:
    def __init__(self):
        self.components_dict: Dict[str, ElementClass] = {}
        self.components_location: List[List[str]] = []
        _logger.info("梯形图组件已初始化完毕")
           
    def add_component(self, component: ElementClass):
        
        self.components_dict[component.id] = component
        self.sort_components()
        valid = self._validate_connections()
        _logger.info(f"梯形图组件已添加：{component.id}")
        return valid
    
    def sort_components(self):
        components = list(self.components_dict.values())
        if not components:
            self.components_location = []
            return
        
        y_groups = {}
        for component in components:
            y = component.bbox[1]
            if y not in y_groups:
                y_groups[y] = []
            y_groups[y].append(component)
        
        sorted_y_groups = sorted(y_groups.items(), key=lambda item: item[0])

        self.components_location = []

        for y, group_components in sorted_y_groups:
            sorted_components = sorted(group_components, key=lambda component: component.bbox[0])
            row = [component.id for component in sorted_components]
            self.components_location.append(row)
        _logger.info(f"梯形图组件已排序：{self.components_location}")

    
    def clear(self):
        self.__init__()
    
    def _validate_connections(self) -> List[str]:
        illegal_components = []
        
        for component in self.components_dict.values():
            if component.dtype == LadderComponents.CONNECT_UP:
                if not self._is_upward_connection_legal(component):
                    illegal_components.append(component.id)
            
            elif component.dtype == LadderComponents.CONNECT_DOWN:
                if not self._is_downward_connection_legal(component):
                    illegal_components.append(component.id)
            
            elif component.dtype == LadderComponents.COIL:
                if not self._is_coil_right_legal(component):
                    illegal_components.append(component.id)
                    
        return illegal_components
    
    def _is_coil_right_legal(self, coil_component: ElementClass) -> bool:
        component_row, component_col = self._find_component_position(coil_component.id)
        if component_row != -1 and component_col != -1:
            row_components = self.components_location[component_row]
            if component_col + 1 < len(row_components):
                return False
        return True

    def _is_upward_connection_legal(self, up_component: ElementClass) -> bool:
        up_component_row, up_component_col = self._find_component_position(up_component.id)
        
        if up_component_row == -1 or up_component_col == -1:
            return False

        if up_component_row == 0:

            return False
        
        has_downward_in_same_row = False
        if up_component_row < len(self.components_location):
            row_components = self.components_location[up_component_row]
            for col_idx, component_id in enumerate(row_components):
                if col_idx > up_component_col:
                    component = self.components_dict.get(component_id)
                    if component and component.dtype == LadderComponents.CONNECT_DOWN:
                        has_downward_in_same_row = True
                        break
        
  
        if not has_downward_in_same_row and up_component_row < len(self.components_location):
            row_components = self.components_location[up_component_row]
            for col_idx, component_id in enumerate(row_components):
                if col_idx > up_component_col:  
                    component = self.components_dict.get(component_id)
                    if component and component.dtype == LadderComponents.CONNECT_UP:
                        return False 

        if up_component.target:
            target_component_id = up_component.target
            target_component = self.components_dict.get(target_component_id)
            
            if not target_component:
                return False
                
            target_row, target_col = self._find_component_position(target_component_id)
            
            if target_row == -1 or target_col == -1:
                return False
                
            if target_row >= up_component_row:
                return False
                
            if target_col > up_component_col:
                return False
                
            if not self._is_connection_path_clear(up_component_row, up_component_col, 
                                                target_row, target_col):
                return False
        
        return True

    def _is_connection_path_clear(self, up_row: int, up_col: int, target_row: int, target_col: int) -> bool:
        
        for row_idx in range(target_row + 1, up_row):
            if row_idx < len(self.components_location):
                row = self.components_location[row_idx]
                if target_col < len(row):
                    component_id = row[target_col]
                    if component_id:
                        component = self.components_dict.get(component_id)
                        if component and component.dtype != LadderComponents.CONNECT_DOWN:
                            return False
        return True
    
    def _find_component_position(self, component_id: str) -> Tuple[int, int]:
        for row_idx, row in enumerate(self.components_location):
            for col_idx, cid in enumerate(row):
                if cid == component_id:
                    return row_idx, col_idx
        return -1, -1
    

    def _is_downward_connection_legal(self, down_component: ElementClass) -> bool:
        component_row, component_col = self._find_component_position(down_component.id)
        
        if component_row == -1 or component_col == -1:
            return False
        
        if component_row >= len(self.components_location) - 1:
            return False
        
        return True
    
class LadderGroup:
    def __init__(self):
            self.group : Dict[int, RungCommand] = {}
        
    def add_ladder(self, 
                    rung: int,
                    ladder: RungCommand):
        if rung in self.group: return
        self.group[rung] = ladder
        
    def work_on_ladder(self, rung: int):
        if rung not in self.group: 
            self.group[rung] = RungCommand()
        return self.group.get(rung)
        
    @property
    def get_compile_queue(self):
        compile_queue = []
        for rung in sorted(self.group.keys()):
            compile_queue.append(self.group[rung])
        return compile_queue
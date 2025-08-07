from core.core import app, udp_manager
from fastapi import APIRouter
from typing import Dict, Tuple, List
from dataclasses import dataclass

router = APIRouter(prefix="/api/ladder", tags=["ladder"])

# 元件类型
@dataclass(frozen=True)
class LadderComponents:
    NORMAL_OPEN = 'normal_open'
    NORMAL_CLOSED = 'normal_closed'
    COIL = 'coil'
    CONNECT_UP = 'connect_up'
    CONNECT_DOWN = 'connect_down'

# 元件信息类
@dataclass
class ElementClass:
    id: hex
    bbox: Tuple[int, int, int, int]
    dtype: str

class LadderCommand:
    def __init__(self):
        self.components_dict: Dict[hex, ElementClass] = {}
        self.components_location: List[List[hex]] = []
        self._component_pin = Dict[int, int] = {}

    def add_component(self, component: ElementClass):
        self.components_dict[component.id] = component
        self.sort_components()
    
    def del_component(self, component: ElementClass):
        if component.id in self.components_location:
            self.components_location.remove(component.id)
            self.sort_components()
        else:
            return
    
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

ladder_command = LadderCommand()
@router.post("/components/ladder/add")
async def add_component(component: Dict):
    ladder_element = ElementClass(id=component["id"],
                                  bbox=component["bbox"],
                                  dtype=component["dtype"])
    ladder_command.add_component(ladder_element)

@router.post("/components/ladder/delete")
async def del_component(component: Dict):
    ladder_command.del_component(component["id"])

app.include_router(router)
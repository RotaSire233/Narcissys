from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class LadderBase:
    def __init__(self,
                 nodes: Any,
                 next: Any):
        self.convert: Dict[Any] = {}
        self.nodes = nodes
        self.next: LadderBase = next

    def run_nodes(self):
        if self.nodes.next is not None:
            self.nodes(self.convert)
    
    def add_convert(self, key: Any, value: Any):
        """
        添加传递数据
        """
        self.convert[key] = value
    
    def del_convert(self, key: Any):
        """
        删除传递数据
        """
        del self.convert[key]

    def next_node(self):
        """
        将数据传递给下一个节点
        """
        if self.next is not None and hasattr(self.next, 'previous_node'):
            self.next.previous_node(self.convert)
    
    def previous_node(self, convert: Dict[Any]):
        """
        从上一个节点接收数据
        """
        self.convert = convert

class ComponentBase:
    def __init__(self,
                 convert: Dict[Any],
                 next: Any):
        
        self.next = next
        

           





    

        
    


        

import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import json

@dataclass
class CommonStructure:
    name: str
    url: str
    stream: bool = False
    dtype: str = 'common'
    input_struct = List[Dict[str, Any]]
    output_struct = List[Dict[str, Any]]

class ApiManager:
    def __init__(self):
        self.apis: Dict[str, CommonStructure] = {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def init_session(self):
        """初始化HTTP会话"""
        if not self.session:
            self.session = aiohttp.ClientSession()
    
    async def close_session(self):
        """关闭HTTP会话"""
        if self.session:
            await self.session.close()
            self.session = None
    
    def add_api(self, api_struct: CommonStructure) -> bool:
        """添加API到管理器"""
        self.apis[api_struct.name] = api_struct
        return True
    
    def remove_api(self, name: str) -> bool:
        """根据名称移除API"""
        if name in self.apis:
            del self.apis[name]
            return True
        return False
    
    def get_api(self, name: str) -> Optional[CommonStructure]:
        """获取特定API信息"""
        return self.apis.get(name)
    
    def list_apis(self) -> List[str]:
        """列出所有API名称"""
        return list(self.apis.keys())
    
    async def call_api(self, name: str, data: Dict[str, Any], callback: Optional[Callable] = None):
        """异步调用指定的API"""
        await self.init_session()
        api = self.get_api(name)
        if not api:
            raise ValueError(f"API {name} not found")
        
        try:
            async with self.session.post(api.url, json=data, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                result = await response.json()
                
                if callback:
                    await callback(name, result)
                    
                return result
        except Exception as e:
            error_result = {"error": str(e)}
            if callback:
                await callback(name, error_result)
            raise ConnectionError(f"Failed to call API {name}: {str(e)}")
    
    async def call_api_background(self, name: str, data: Dict[str, Any], callback: Optional[Callable] = None):
        """在后台异步调用API，不等待结果"""
        asyncio.create_task(self.call_api(name, data, callback))
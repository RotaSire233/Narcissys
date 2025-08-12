from openai import OpenAI, AsyncOpenAI
from typing import List, Dict
import json
import os
import httpx
import asyncio
from dataclasses import dataclass
from asyncio import Semaphore
from loguru import logger as _logger

@dataclass(frozen=True)
class SupportList:
    sil = ("siliconflow","https://api.siliconflow.cn/v1")
    pad = ("paddle", "")
    ope = ("openai", "")
    zhi = ("zhipu", "")
    qwn = ("qwen", "")
    dif = ("dify", "")

@dataclass
class KeyView:
    key: str
    url: str

class ApiKeys:
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), "keys/api_key.json"), "r") as self.f:
            self.keys_json: Dict = json.load(self.f)
        self.info: Dict[str, KeyView] = {}
        self.info["sil"]= KeyView(self.keys_json["siliconflow"],
                                   SupportList.sil[1])

        self.info["qwe"] = KeyView(self.keys_json["qwen"],
                             SupportList.qwn[1])
        
        self.info["ope"] = KeyView(self.keys_json["openai"],
                                 SupportList.ope[1])
        
        self.info["zhi"] = KeyView(self.keys_json["zhipu"],
                               SupportList.zhi[1])
        
        self.info["pad"] = KeyView(self.keys_json["paddle"],
                               SupportList.pad[1])
        
        self.info["dif"] = KeyView(self.keys_json["dify"],
                               SupportList.dif[1])
    

    def get_api_key(self, api_name: str) -> str:
        """
        根据api_name获取对应的api key
        """
        return self.info.get(api_name)
    
    def update_api_key(self, api_name: str, api_key: str):
        """
        更新api key
        """
        self.keys_json[api_name] = api_key
        self.__init__()
        datas = json.dump(self.keys_json)
        self.f.write(datas)

class ApiConfig:
    api_key: str
    base_url: str
    max_concurrent: int = 10
    def __init__(self):
        if self.api_key is not None or self.base_url is not None:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            self.semaphore = Semaphore(self.max_concurrent)
        else:
            raise ValueError("Please set your API key and base URL.")

class ClientBase:
    def __init__(self, api_config: ApiConfig):
        self.api_config = api_config
        self.client = api_config.client
        self.model_dict = self.list_models()
        self.cur_model = None
        self.system_prompt = None
        self.stream = False

    def list_models(self):
        try:
            models = self.client.models.list()
            return {model.id for model in models.data}
            
        except Exception as e:
            _logger.error(f"获取模型列表时出错: {e}")
            return {}
    def set_model(self, model_id: str):
        self.cur_model = self.model_dict.get(model_id, None)

    def set_system_prompt(self, system_prompt: str):
        self.system_prompt = system_prompt

    async def chat_stream(self, prompt: List[Dict[str, str]]):
        # 使用信号量控制并发
        if self.stream:
            async with self.api_config.semaphore:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_config.base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_config.api_key}"},
                        json={
                            "model": self.cur_model,
                            "messages": prompt,
                            "stream": self.stream
                        }
                    )
                    
                    async for chunk in response.aiter_text():
                        content = chunk.strip()
                        if content:
                            return content

    async def chat_completion(self, prompt: List[Dict[str, str]]):
        # 使用信号量控制并发
        async with self.api_config.semaphore:
            try:
                response = await self.client.chat.completions.create(
                    model=self.cur_model,
                    messages=prompt,
                    stream=self.stream
                )
                return response
            except Exception as e:
                _logger.error(f"API调用出错: {e}")
                raise 

    
    




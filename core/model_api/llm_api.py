from openai import OpenAI, AsyncOpenAI
from typing import List, Dict
import json
import os
import httpx
import asyncio
from dataclasses import dataclass
from asyncio import Semaphore
from loguru import logger as _logger
import uuid


@dataclass(frozen=True)
class SupportList:
    sil = ("siliconflow", "https://api.siliconflow.cn/v1")
    ope = ("openai", "https://api.openai.com/v1")
    zhi = ("zhipu", "https://open.bigmodel.cn/api/paas/v4/")
    qwn = ("qwen", "https://dashscope.aliyuncs.com/compatible-mode/v1")

@dataclass
class KeyView:
    key: str
    url: str

@dataclass
class LlmResponse:
    model_name: str
    prompt: List[Dict[str, str]]
    stream: bool


class ApiKeys:
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), "keys/api_key.json"), "r") as self.f:
            self.keys_json: Dict = json.load(self.f)
        self.info: Dict[str, KeyView] = {}
        self.info["siliconflow"]= KeyView(self.keys_json["siliconflow"],
                                   SupportList.sil[1])

        self.info["qwen"] = KeyView(self.keys_json["qwen"],
                             SupportList.qwn[1])
        
        self.info["openai"] = KeyView(self.keys_json["openai"],
                                 SupportList.ope[1])
        
        self.info["zhipu"] = KeyView(self.keys_json["zhipu"],
                               SupportList.zhi[1])
        
    def get_api_info(self, api_name: str) -> str:
        """
        根据api_name获取对应的api key
        """
        return self.info.get(api_name)
    
    def update_api_key(self, api_name: str, api_key: str):
            """
            更新api key
            """
            self.keys_json[api_name] = api_key
            with open(os.path.join(os.path.dirname(__file__), "keys/api_key.json"), "w") as f:
                json.dump(self.keys_json, f, indent=2)
            self.__init__()

class ApiConfig:
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.max_concurrent: int = 10
        if self.api_key is not None and self.base_url is not None:
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
            self.semaphore = Semaphore(self.max_concurrent)
        else:
            self.client = None
            self.semaphore = None

class ClientBase:
    def __init__(self, api_config: ApiConfig, system_prompt: str = None):
        self.api_config = api_config
        self.client = api_config.client
        self.system_prompt = system_prompt
        self.message = None
        self.done = False

    def _prepare_messages(self, prompt: List[Dict[str, str]]) -> List[Dict[str, str]]:
        if self.system_prompt:
            has_system = any(msg.get('role') == 'system' for msg in prompt)
            if not has_system:
                return [{"role": "system", "content": self.system_prompt}] + prompt
        return prompt

    async def chat_stream(self, response_struct: LlmResponse):
        self.done = False
        messages = self._prepare_messages(response_struct.prompt)
        
        if response_struct.stream:
            async with self.api_config.semaphore:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.api_config.base_url}/chat/completions",
                        headers={"Authorization": f"Bearer {self.api_config.api_key}"},
                        json={
                            "model": response_struct.model_name,
                            "messages": messages,
                            "stream": response_struct.stream
                        }
                    )
                    
                    async for chunk in response.aiter_text():
                        content = chunk.strip()
                        if content:
                            yield content
                    self.done = True

    async def chat_completion(self, response_struct: LlmResponse):
        self.done = False
        messages = self._prepare_messages(response_struct.prompt)
        
        async with self.api_config.semaphore:
            try:
                response = await self.client.chat.completions.create(
                    model=response_struct.model_name,
                    messages=messages,
                    stream=response_struct.stream
                )
                self.done = True
                self.message = response
            except Exception as e:
                _logger.error(f"API调用出错: {e}")
                self.done = True
                raise

class ClientGroup:
    def __init__(self):
        self.clients: Dict[str, ClientBase] = {}

    def regist_task(self, ClientBase: ClientBase):
        task_id = str(uuid.uuid4())
        self.clients[task_id] = ClientBase

        return task_id
from openai import OpenAI 
from utils.logger import log
from typing import List, Dict
import json
import os
import httpx
import asyncio


_logger = log.get_child_logger(__name__)


class ApiKeys:
    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), "keys/api_keys.json"), "r") as f:
            self.keys_json: Dict = json.load(f)
        _logger.info(f"Loaded {len(self.keys_json.keys())} API keys")
        self.siliconflow_key = self.keys_json["siliconflow"]
        self.siliconflow_url = "https://api.siliconflow.cn/v1"
        self.qwen_key = self.keys_json["qwen"]
        self.qwen_url = None
        self.paddle_key = self.keys_json["paddle"]
        self.paddle_url = None
        self.openai_key = self.keys_json["openai"]
        self.openai_url = None
        self.dify_key = self.keys_json["dify"] 
        self.dify_url = None
        self.zhipu_key = self.keys_json["zhipu"]
        self.zhipu_url = None


class ApiConfig:
    api_key: str
    base_url: str
    model: str
    def __init__(self):
        if self.api_key is not None or self.base_url is not None:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            _logger.info("API密钥,URL已设置。")
        else:
            raise ValueError("Please set your API key and base URL.")

class ClientBase:
    def __init__(self, api_config: ApiConfig):
        self.api_config = api_config
        self.client = api_config.client
        self.model = api_config.model
        self.system_prompt = None
        self.callback = None
        self.stream = False
    def set_system_prompt(self, system_prompt: str):
        self.system_prompt = system_prompt

    def set_call_back(self, callback: callable):
        self.callback = callback
    
    def set_stream(self, stream: bool):
        self.stream = stream

    async def stream_call(self, prompt: List[Dict[str, str]]):
        async with httpx.AsyncClient(api_key=self.api_config.api_key, base_url=self.api_config.base_url) as client:
            response = await client.post(
                "/chat/completions",
                json={
                    "model": self.model,
                    "messages": prompt,
                    "stream": self.stream
                }
            )
            
            async for chunk in response.aiter_text():
                content = chunk.strip()
                if content:
                    self.callback(content=content)

    
    




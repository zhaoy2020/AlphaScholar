from dataclasses import dataclass, field
import os
import openai
from typing import Optional, Literal


@dataclass
class Config:
    # 平台密钥
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    CAU_API_KEY: str = os.getenv("CAU_API_KEY", "")
    LOCAL_API_KEY: str = os.getenv("LOCAL_API_KEY", "EMPTY")   # 本地服务通常不需要key

    # 平台地址
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"        # 或你的代理地址
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    CAU_BASE_URL: str = "https://openai.cau.edu.cn/v1"
    LOCAL_BASE_URL: str = "http://localhost:8000/v1"

    platform: Literal["openai", "deepseek", "cau", "local"] = "local"

    model: Literal["gpt-4o", "deepseek-chat", "qwen3.6"] = 'qwen3.6'

    def create_client(self) -> openai.OpenAI:
        """根据配置创建 OpenAI 兼容客户端"""

        if self.platform == "openai":
            base_url = self.OPENAI_BASE_URL
            api_key = self.OPENAI_API_KEY

        elif self.platform == "deepseek":
            base_url = self.DEEPSEEK_BASE_URL
            api_key = self.DEEPSEEK_API_KEY

        elif self.platform == "cau":
            base_url = self.CAU_BASE_URL
            api_key = self.CAU_API_KEY

        else:  # local
            base_url = self.LOCAL_BASE_URL
            api_key = self.LOCAL_API_KEY

        return openai.OpenAI(api_key=api_key, base_url=base_url)
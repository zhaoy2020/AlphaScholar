from dataclasses import dataclass, field
import os
import openai
from typing import Optional, Literal


@dataclass
class Config:
    platform: Literal["openai", "deepseek", "cau", "local"] = "local"
    async_model: bool = False  # 是否使用异步模型接口（如 OpenAI 的 streaming）
    # URL 和 API_KEY
    url_dict: dict = field(default_factory=lambda: {
        "openai": ["https://api.openai.com/v1", os.getenv("OPENAI_API_KEY", ""), 'gpt-4o'],
        "deepseek": ["https://api.deepseek.com", os.getenv("DEEPSEEK_API_KEY", ""), 'deepseek-v4-flash'],
        "cau": ["https://openai.cau.edu.cn/v1", os.getenv("CAU_API_KEY", ""), 'qwen3.6'],
        "local": ["http://localhost:8000/v1", os.getenv("LOCAL_API_KEY", "EMPTY"), '/bmp/backup/zhaosy/ProgramFiles/hf/qwen/Qwen3.6-27B'],
    })

    def create_client_and_model(self) -> tuple[openai.OpenAI, str]:
        """根据配置创建 OpenAI 兼容客户端和模型"""

        if self.platform not in self.url_dict.keys():
            raise ValueError(f"Unsupported platform: {self.platform}")
        else:
            base_url, api_key, model = self.url_dict[self.platform]
            if self.async_model:
                return (openai.OpenAI(base_url=base_url, api_key=api_key, timeout=60, stream=True), model)
            else:
                return (openai.OpenAI(base_url=base_url, api_key=api_key), model)
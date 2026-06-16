from dataclasses import dataclass, field 
import os


@dataclass
class Config:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "EMPTY")
    OPENAI_BASE_URL: str = "https://openai.cau.edu.cn/v1"
    MODEL: str = "qwen3.6"   # 或者 "deepseek-chat", "gpt-4o" 等
    
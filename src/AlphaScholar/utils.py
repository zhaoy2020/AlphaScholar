

from typing import Literal
from loguru import logger 

import json
import uuid
from datetime import datetime, timezone


def show(message: str, method: Literal['print', 'logger'] = 'print'):
    """统一的输出接口，支持不同的输出方式"""

    if method == 'print':
        print(message, flush=True, end='')  # flush=True 确保实时输出，end='' 避免自动换行

    elif method == 'logger':
        logger.info(message)
        
    else:
        raise ValueError(f"Unsupported output method: {method}")
    


def argparser():
    """解析命令行参数的函数，返回一个包含所有参数的对象"""

    import argparse

    parser = argparse.ArgumentParser(description="AlphaScholar: A versatile tool for academic research.")
    
    # 添加命令行参数
    parser.add_argument('--agent', type=str, default='two', help='智能体选择，如two、multi')
    parser.add_argument('--platform', type=str, default='local', help='API平台选择，如openai、deepseek、cau、local')
    parser.add_argument('--report_path', type=str, default='./reports/report.md', help='输出文件路径')
    parser.add_argument('--log_path', type=str, default='./logs/training_data.json', help='训练数据日志文件路径')
    
    return parser.parse_args()


class TrainingLogger:
    '''记录聊天过程的数据，方便后续分析和训练。'''

    def __init__(self, log_path: str = 'training_data.json'):
        self.log_path = log_path
        self.current_session = None

    def make_serializable(self, obj):
        if hasattr(obj, "model_dump"):
            return obj.model_dump(exclude_unset=True)
        if isinstance(obj, dict):
            return {k: self.make_serializable(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.make_serializable(v) for v in obj]
        return obj

    def start_session(self, user_query: str, model_config: dict):
        self.current_session: dict = {
            'session_id': str(uuid.uuid4()),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'user_query': user_query,
            'conversation': [],
            'final_report': '',
            'evaluations': [],
            'user_feedback': [],
            'model_config': model_config,
        }

    def log_conversation(self, messages):
        '''记录完整的历史，每次更新覆盖'''

        if self.current_session is not None:
            self.current_session['conversation'] = self.make_serializable(messages)

    def log_tool_call(self, tool_name):
        """记录使用的工具"""

        if self.current_session and tool_name not in self.current_session["tools_used"]:
            self.current_session["tools_used"].append(tool_name)

    def log_evaluation(self, score, issues, suggestion):
        """记录一轮评审结果"""

        if self.current_session:
            self.current_session["evaluations"].append({
                "score": score,
                "issues": issues,
                "suggestion": suggestion
            })

    def log_final_report(self, report_text):
        """记录最终报告"""

        if self.current_session:
            self.current_session["final_report"] = report_text

    def end_session(self):
        """结束会话并写入文件"""

        if not self.current_session:
            return
        # 隐私过滤（脱敏）可在此处处理
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(self.current_session, ensure_ascii=False) + "\n")
        self.current_session = None
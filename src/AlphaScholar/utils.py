

from typing import Literal
from loguru import logger 


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
    
    return parser.parse_args()
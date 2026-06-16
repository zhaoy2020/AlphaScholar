

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
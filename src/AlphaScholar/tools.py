'''
Function calling (Tool calling):
- 目标：打破纯文本交互的限制，让模型能够触发外部操作（查数据库、调 API、执行计算等）。

- 工作方式：
  - 你预先定义一系列函数（工具），包括函数名、功能描述、参数类型。
  - 用户提问后，模型分析上下文，如果觉得需要调用某个函数，就返回一个结构化的调用请求（JSON）。
  - 你的程序真正执行这个函数，得到结果。
  - 将结果重新喂给模型，模型再基于结果生成最终回答。

- 字段说明：
  - type: "function"（表示这是一个函数调用工具）
  - function.name	函数名，唯一标识
  - function.description	用自然语言描述函数的作用（至关重要，模型靠这个决定何时调用）
  - function.parameters	JSON Schema，定义函数的输入参数

例如：
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取指定城市的天气",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["city"]
        }
    }
}

Function calling 和 MCP（Model-Callable Programs）的关系：
- 没有 MCP 时：你直接在 tools.py 里写死工具定义和 Python 函数，通过 Function Calling 让模型调用它们。
- 引入 MCP 时：
  - 你把 search_pubmed、search_arxiv 等函数封装成一个 MCP Server（之前我用 FastMCP 演示过）。
  - 你的 Agent 在启动时，通过 MCP 客户端连接到这个 Server，调用 list_tools() 动态获取工具列表。
  - 将获取到的工具定义转换成 OpenAI 的 tools 格式，传给模型进行 Function Calling。
  - 当模型返回 tool_calls 时，你的 Agent 再通过 MCP 客户端的 call_tool 去执行真正的函数，并将结果以 tool 消息返回给模型。
'''


import json
import requests
from pymed import PubMed
import arxiv
import os 
from pathlib import Path 


PUBMED_EMAIL = os.getenv("EMAIL", 'example@gmail.com') # 请改成真实邮箱


def search_pubmed(query: str, max_results: int = 5) -> str:
    """在 PubMed 中检索生物医学文献"""

    try:
        pubmed = PubMed(tool="LiteratureAgent", email=PUBMED_EMAIL)
        results = pubmed.query(query, max_results=max_results)
        articles = []
        for article in results:
            title = article.title
            authors = ', '.join([a['lastname'] for a in article.authors[:3]])
            pub_date = str(article.publication_date)
            abstract = (article.abstract[:300] + "...") if article.abstract else "无摘要"
            articles.append({
                "title": title,
                "authors": authors,
                "date": pub_date,
                "abstract": abstract,
            })
        return json.dumps(articles, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return f"PubMed 检索出错: {str(e)}"


def search_arxiv(query: str, max_results: int = 5) -> str:
    """在 arXiv 中检索预印本"""

    try:
        client = arxiv.Client()
        search = arxiv.Search(query=query, max_results=max_results,
                              sort_by=arxiv.SortCriterion.Relevance)
        results = client.results(search)
        articles = []
        for r in results:
            articles.append({
                "title": r.title,
                "authors": ', '.join([a.name for a in r.authors[:3]]),
                "date": str(r.published),
                "abstract": (r.summary[:300].replace('\n', ' ')) + "...",
            })
        return json.dumps(articles, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return f"arXiv 检索出错: {str(e)}"


def search_semantic_scholar(query: str, max_results: int = 5) -> str:
    """在 Semantic Scholar 中检索全学科论文"""

    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,authors,year,abstract"
        }
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        articles = []
        for paper in data.get("data", []):
            authors = ', '.join([a['name'] for a in paper.get("authors", [])[:3]])
            abstract = paper.get("abstract") or "无摘要"
            articles.append({
                "title": paper.get("title", "未知"),
                "authors": authors,
                "date": paper.get("year", "未知"),
                "abstract": abstract[:300] + ("..." if len(abstract) > 300 else ""),
            })
        return json.dumps(articles, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return f"Semantic Scholar 检索出错: {str(e)}"
    

def scan_local_files(directory: str) -> str:
    """扫描本地目录下的文件，返回文件列表和基本信息"""

    try:
        directory: Path = Path(directory)
        files_info = []
        for file in directory.glob("*.*"):
            if file.is_file():
                files_info.append({
                    "filename": file.name,
                    'format': file.suffix,
                    "size_kb": round(file.stat().st_size / 1024, 2),
                    "path": str(file.resolve())
                })
        return json.dumps(files_info, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"扫描目录出错: {str(e)}"
    

def read_pdf(file_path: str) -> str:
    """读取 PDF 文件内容（示例实现，实际可用 PyPDF2、pdfplumber 等库）"""

    try:
        # 这里简单返回文件路径，实际应提取文本内容
        return f"PDF 文件路径: {file_path}"
    
    except Exception as e:
        return f"读取 PDF 出错: {str(e)}"
    
def read_docx(file_path: str) -> str:
    pass
    
def read_txt(file_path: str) -> str:
    """读取 TXT 文件内容"""
    pass 

def read_csv(file_path: str) -> str:
    """读取 CSV 文件内容（示例实现，实际可用 pandas 等库）"""
    pass


def read_file(file_path: str, format: str) -> str:
    '''读取本地文件内容'''

    try:
        read_functions = {
            ".pdf": read_pdf,
            ".docx": read_docx,
            ".txt": read_txt,
            ".csv": read_csv
        }
        articles: list = []
        if format not in read_functions:
            return f"不支持的文件格式: {format}"
        else:
            content = read_functions[format](file_path)
            articles.append({
                "title": content['title'] if content is not None else "未知",
                'authors': content['authors'] if content is not None else "未知",
                'date': content['date'] if content is not None else "未知",
                'abstract': content['abstract'] if content is not None else "未知"
            })
            return json.dumps(articles, ensure_ascii=False, indent=2)

    except Exception as e:
        return f"读取文件出错: {str(e)}"


# --- 工具描述（OpenAI Function Calling 格式）---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_pubmed",
            "description": (
                "概述：在 PubMed 中检索生物医学文献。"
                "使用：支持 PubMed 高级检索语法，包括字段标签（如 [tiab] 标题/摘要、[ta] 期刊名、[au] 作者）、布尔运算符（AND、OR、NOT）和括号。请使用完整的 PubMed 查询表达式，"
                '例如："bacillus"[tiab] AND "ai"[tiab] AND "Nature"[ta]'
                '例如："(bacillus"[tiab] OR "lactobacillus"[tiab]) AND ("ai"[tiab] OR "machine learning"[tiab] OR "deep learning"[tiab]) AND "Nature"[ta]'
                "强调：必须使用高级检索语法，否则结果不准确。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": 'PubMed 查询表达式，可使用字段标签和布尔运算符,例如："bacillus"[tiab] AND "ai"[tiab] AND "Nature"[ta],例如："(bacillus"[tiab] OR "lactobacillus"[tiab]) AND ("ai"[tiab] OR "machine learning"[tiab] OR "deep learning"[tiab]) AND "Nature"[ta]'
                    },
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_arxiv",
            "description": (
                "在 arXiv 中检索预印本。使用简单关键词搜索，支持 AND、OR、NOT 和引号精确匹配。"
                "例如：'variational autoencoder' AND microbiome"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "arXiv 搜索字符串，可包含 AND、OR 和引号"
                    },
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_semantic_scholar",
            "description": (
                "在 Semantic Scholar 中检索全学科论文。使用简单关键词搜索，支持 AND、+ 前缀（必须包含）、- 前缀（排除）。"
                "例如：'variational autoencoder' +microbiome"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Semantic Scholar 查询字符串，可包含 AND、+、- 运算符"
                    },
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        }
    }
]


# 工具名 -> 函数映射
TOOL_FUNCTIONS = {
    "search_pubmed": search_pubmed,
    "search_arxiv": search_arxiv,
    "search_semantic_scholar": search_semantic_scholar,
    "scan_local_files": scan_local_files,
    "read_file": read_file,
}
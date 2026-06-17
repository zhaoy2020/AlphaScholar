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
OpenAI的Client的tools所需工具定义格式如下：
TOOLS = [
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
    },
]

# 模型返回的tool_calls后需要在本地调用：
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
}

# 喂入Client中，模型返回调用请求，本地解析请求并执行，执行结果加入以 tool角色加入 Prompt context中，最后返回给大模型：
response = client.chat.completions.create(
                model=model,
                messages=memory.get_messages(),
                tools=TOOLS,
                tool_choice="auto",
                stream=False,
            )
msg = response.choices[0].message
if msg.tool_calls:
    for tool_call in msg.tool_calls:
        func_name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        result = TOOL_FUNCTIONS[func_name](**args)

        memory.add_message(role='tool', content=result, tool_call_id=tool_call.id)
'''

'''
那么 Function calling 和 MCP（Model-Callable Programs）的关系：
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


# --- 工具描述（OpenAI Function Calling 格式）---
TOOLS: list = []
TOOL_FUNCTIONS: dict = {}


# --- 辅助函数 ---
def func_to_tool(func):
    """将普通函数转换成 OpenAI Function Calling 的工具定义格式"""
    maps: dict = {
        "str": "string",
        "int": "integer",
        "float": "number",
        "bool": "boolean",
    }
    
    doc = func.__doc__
    arg = doc.find('Args:')
    ret = doc.find('Returns:')
    exam = doc.find('Example:')

    func_desc = doc[:arg] + doc[exam:]
    arg_desc = doc[arg:ret]

    properties: dict = {}
    required: list = []
    for line in arg_desc.split('\n'):
        if line.strip() and not line.strip().startswith('Args:'):
            param_name_type, param_desc = line.strip().split('; ')
            name, type_ = param_name_type.split(': ')
            if '=' in type_:
                # 有默认值的参数
                type_, default = type_.split(' = ')
            else:
                # 没有默认值的参数
                default = None
                required.append(name)

            properties[name] = {
                "type": maps.get(type_, type_),
                "default": default,
                "description": param_desc,
            }
            
    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": func_desc or "",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        }
    }


def tool(func):
    """装饰器，将普通函数转换成工具定义，并注册到 TOOL_FUNCTIONS 中"""
    tool_def = func_to_tool(func)
    TOOLS.append(tool_def)
    TOOL_FUNCTIONS[func.__name__] = func

    return func


# --- 具体工具函数实现 ---
@tool
def search_pubmed(query: str, max_results: int = 5) -> str:
    """
    概述：在 PubMed 中检索生物医学文献。
    使用：支持 PubMed 高级检索语法，包括字段标签（如 [tiab] 标题/摘要、[ta] 期刊名、[au] 作者）、布尔运算符（AND、OR、NOT）和括号。请使用完整的 PubMed 查询表达式，
    例如："bacillus"[tiab] AND "ai"[tiab] AND "Nature"[ta]，
    例如："(bacillus"[tiab] OR "lactobacillus"[tiab]) AND ("ai"[tiab] OR "machine learning"[tiab] OR "deep learning"[tiab]) AND "Nature"[ta]，
    强调：必须使用高级检索语法，否则结果不准确。
    Args:
        query: str; PubMed 查询表达式，可使用字段标签和布尔运算符, 例如："bacillus"[tiab] AND "ai"[tiab] AND "Nature"[ta]，例如："(bacillus"[tiab] OR "lactobacillus"[tiab]) AND ("ai"[tiab] OR "machine learning"[tiab] OR "deep learning"[tiab]) AND "Nature"[ta]
        max_results: int = 5; 最大返回结果数
    Returns:
        str: JSON 字符串，包含检索到的文献列表格。
    Example:
        search_pubmed('("variational autoencoder"[tiab] OR "VAE"[tiab]) AND "microbiome"[tiab]', max_results=3)
    """

    PUBMED_EMAIL = os.getenv("EMAIL", 'example@gmail.com') # 请改成真实邮箱
    try:
        pubmed = PubMed(tool="LiteratureAgent", email=PUBMED_EMAIL)
        results = pubmed.query(query, max_results=max_results)
        articles = []
        for article in results:
            title = article.title
            authors = ', '.join([a['lastname'] for a in article.authors[:30]])
            pub_date = str(article.publication_date)
            abstract = (article.abstract + "...") if article.abstract else "无摘要"
            doi = article.doi if article.doi else "未知"
            pmid = article.pubmed_id if article.pubmed_id else "未知"
            journal = article.journal if article.journal else "未知"
            articles.append({
                "title": title,
                "authors": authors,
                "date": pub_date,
                "abstract": abstract,
                "doi": doi,
                "pmid": pmid,
                "journal": journal,
            })
        return json.dumps(articles, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return f"PubMed 检索出错: {str(e)}"


@tool
def search_arxiv(query: str, max_results: int = 5) -> str:
    """在 arXiv 中检索预印本。
    概述：在 arXiv 中检索预印本论文，涵盖物理学、数学、计算机科学、生物学、金融等多个学科。
    使用：支持简单关键词搜索，可使用布尔运算符（AND、OR、NOT）组合多个概念，也可使用英文双引号 "" 进行精确短语匹配。
    例如："variational autoencoder" AND microbiome，
    例如："graph neural network" OR "message passing" AND "drug discovery"，
    强调：请优先使用含义明确的关键词，若用布尔运算符请大写，用引号包裹固定短语以提高查准率。
    Args:
        query: str; arXiv 搜索字符串，可包含 AND、OR、NOT 和英文双引号 ""。
        max_results: int = 5; 最大返回结果数
    Returns:
        str: JSON 字符串，包含检索到的文献列表（标题、作者、日期、摘要）。
    Example:
        search_arxiv('"variational autoencoder" AND microbiome', max_results=3)
    """

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
                # "abstract": (r.summary[:300].replace('\n', ' ')) + "...",
                "abstract": (r.summary.replace('\n', ' ')) + "...",
            })
        return json.dumps(articles, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return f"arXiv 检索出错: {str(e)}"


@tool
def search_semantic_scholar(query: str, max_results: int = 5) -> str:
    """在 Semantic Scholar 中检索全学科论文。
    概述：在 Semantic Scholar 中检索全学科论文，适合作为 Google Scholar 的替代。
    使用：支持简单关键词搜索，可使用布尔运算符（AND、OR、NOT）组合概念。还支持 + 前缀表示必须包含该词，- 前缀表示排除该词。建议使用英文双引号 "" 进行精确短语匹配。
    例如："variational autoencoder" +microbiome，
    例如："graph neural network" -"image classification" AND "drug discovery"，
    强调：使用 + 和 - 运算符时不要留空格（如 +microbiome），布尔运算符 AND、OR 需要前后空格。
    Args:
        query: str; Semantic Scholar 搜索字符串，可包含 AND、OR、NOT、+、- 运算符和英文双引号 ""。
        max_results: int = 5; 最大返回结果数
    Returns:
        str: JSON 字符串，包含检索到的文献列表（标题、作者、年份、摘要）。
    Example:
        search_semantic_scholar('"variational autoencoder" +microbiome', max_results=5)
    """

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
                # "abstract": abstract[:300] + ("..." if len(abstract) > 300 else ""),
                "abstract": abstract + ("..." if len(abstract) > 300 else ""),
            })
        return json.dumps(articles, ensure_ascii=False, indent=2)
    
    except Exception as e:
        return f"Semantic Scholar 检索出错: {str(e)}"
    

# @tool 
def search_google_scholar(query: str, max_results: int = 5) -> str:
    """在 Google Scholar 中检索论文（示例实现，实际可用 scholarly 等库）"""
    pass
    

# @tool
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


# @tool
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


if __name__ == "__main__":
    # 简单测试工具函数
    print(search_pubmed('("variational autoencoder"[tiab] OR "VAE"[tiab]) AND ("microbiome"[tiab] OR "microbiota"[tiab])', max_results=5))
    # print(search_arxiv('"variational autoencoder" AND microbiome', max_results=2))
    # print(search_semantic_scholar('variational autoencoder +microbiome', max_results=2))
    # print(f'TOOLS: {json.dumps(TOOLS, ensure_ascii=False, indent=2)}')
    # print(f'\n\n --- TOOLS --- \n\n {TOOLS}')
    # print(f'\n\n --- TOOL_FUNCTIONS --- \n\n {list(TOOL_FUNCTIONS.keys())}')

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
        if format in read_functions:
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


# 工具描述（OpenAI Function Calling 格式）
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_pubmed",
            "description": "在 PubMed 中检索生物医学、药学、护理等生命科学文献。适合医学相关研究。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索词，如 'cancer immunotherapy'"},
                    "max_results": {"type": "integer", "description": "返回数量，默认5"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_arxiv",
            "description": "在 arXiv 中检索计算机科学、物理、数学等领域的预印本。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索词"},
                    "max_results": {"type": "integer"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_semantic_scholar",
            "description": "在 Semantic Scholar 中检索全学科论文，适合作为 Google Scholar 的替代。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索词"},
                    "max_results": {"type": "integer"}
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
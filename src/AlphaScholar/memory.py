from pathlib import Path 
import json
from typing import Dict, List 


class ShortTermMemory:
    """Short-term memory for the agent.

    Example:
        # 原本手动维护 messages 列表
        # 现在全部替换为 memory 操作
        memory.add_message("system", SYSTEM_PROMPT)
        memory.add_message("user", user_input)

        # 工具调用后
        memory.add_message("tool", tool_result, tool_call_id=tc.id)

        # 报告生成后
        memory.add_message("assistant", full_response)
    """
    
    def __init__(self):
        self.messages: list[dict] = []  # 存储对话消息

    def add_message(self, role: str, content: str, **kwargs):
        """添加消息到短期记忆, role: 'user', 'assistant', 'tool'"""
        msg: dict = {"role": role, "content": content}
        msg.update(kwargs)
        self.messages.append(msg)

    def get_messages(self) -> list[dict]:
        """获取当前的消息列表"""
        return self.messages
    
    def clear(self):
        """清空短期记忆"""
        self.messages.clear()


class LongTermMemory:
    """Long-term memory for the agent.
    
    1. 存储文献和报告
    2. 支持查询和语义检索
    """

    def __init__(self, storage_path: str = 'long_term_memory.json'):
        self.storage_path: Path = Path(storage_path)
        if not self.storage_path.exists():
            self._save({"papers": [], "reports": []})  # 初始化空数据

    def _load(self):
        """从文件加载长期记忆数据"""
        if self.storage_path.exists():
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def _save(self, data: dict):
        """将当前数据保存到文件"""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_paper(self, title: str, source: str, abstract: str = "",
                  authors: str = "", year: int = None,
                  keywords: str = "", research_topic: str = "") -> int:
        """添加一篇论文，返回在列表中的索引"""
        data = self._load()
        paper = {
            "title": title,
            "source": source,
            "abstract": abstract,
            "authors": authors,
            "year": year,
            "keywords": keywords,
            "research_topic": research_topic
        }
        data["papers"].append(paper)
        self._save(data)

        return len(data["papers"]) - 1

    def search_papers(self, keyword: str = "", source: str = None, limit: int = 10) -> List[Dict]:
        """简单搜索：标题/摘要/关键词包含关键字（忽略大小写）"""
        data = self._load()
        results = []
        for paper in data["papers"]:
            if source and paper.get("source") != source:
                continue
            if keyword:
                kw = keyword.lower()
                text = (paper.get("title", "") + " " +
                        paper.get("abstract", "") + " " +
                        paper.get("keywords", "")).lower()
                if kw not in text:
                    continue
            results.append(paper)
            if len(results) >= limit:
                break

        return results 
    
    def list_all_papers(self) -> List[Dict]:
        return self._load()["papers"]

    def add_report(self, query: str, report_text: str,
                   score: int = None, paper_ids: List[int] = None):
        data = self._load()
        report = {
            "query": query,
            "report_text": report_text,
            "score": score,
            "paper_ids": paper_ids or []
        }
        data["reports"].append(report)
        self._save(data) 

    def search_reports(self, keyword: str = "", limit: int = 5) -> List[Dict]:
        data = self._load()
        results = []
        for report in data["reports"]:
            if keyword and keyword.lower() not in report.get("query", "").lower():
                continue
            results.append(report)
            if len(results) >= limit:
                break

        return results

    def list_all_reports(self) -> List[Dict]:
        return self._load()["reports"]
    
    def clear(self):
        self._save({"papers": [], "reports": []})


class Memory:
    """Memory management for the agent.
    统一接口，包含短期记忆和长期记忆，当前主要使用短期记忆。
    """

    def __init__(self, storage_path: str = 'long_term_memory.json'):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(storage_path=storage_path)

    def add_message(self, role: str, content: str, **kwargs):
        self.short_term.add_message(role, content, **kwargs)

    def get_messages(self) -> list[dict]:
        return self.short_term.get_messages()
    
    def clear_short_term(self):
        self.short_term.clear()

    def add_paper(self, **kwargs): 
        self.long_term.add_paper(**kwargs)

    def search_papers(self, **kwargs): 
        return self.long_term.search_papers(**kwargs)

    def add_report(self, **kwargs): 
        self.long_term.add_report(**kwargs)

    def search_reports(self, **kwargs): 
        return self.long_term.search_reports(**kwargs)

    
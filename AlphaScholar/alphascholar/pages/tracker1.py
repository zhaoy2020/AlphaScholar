import reflex as rx
from typing import List, Dict, Literal, Optional
import requests
from xml.etree import ElementTree
from openai import OpenAI
import os
import asyncio

from ..templates import web_structure


# --------------------- LLM 配置 -------------------- #
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openai.cau.edu.cn/v1")
MODEL_NAME = "qwen3.6"  # 推荐使用性价比高的模型

client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


# --------------------- 文献检索辅助函数 -------------------- #
def search_on_pubmed(query: str, max_results: int = 5) -> List[Dict]:
    """通过 PubMed E-utilities 检索文献"""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance"
    }
    search_resp = requests.get(f"{base_url}/esearch.fcgi", params=search_params)
    search_resp.raise_for_status()
    id_list = search_resp.json().get("esearchresult", {}).get("idlist", [])

    if not id_list:
        return []

    fetch_params = {
        "db": "pubmed",
        "id": ",".join(id_list),
        "retmode": "xml"
    }
    fetch_resp = requests.get(f"{base_url}/efetch.fcgi", params=fetch_params)
    fetch_resp.raise_for_status()
    root = ElementTree.fromstring(fetch_resp.content)

    articles = []
    for article in root.findall(".//PubmedArticle"):
        title = article.findtext(".//ArticleTitle", "")
        abstract = article.findtext(".//AbstractText", "")
        pmid = article.findtext(".//PMID", "")
        authors = [
            f"{a.findtext('ForeName', '')} {a.findtext('LastName', '')}"
            for a in article.findall(".//Author")
            if a.findtext("LastName")
        ]
        journal = article.findtext(".//Journal/Title", "")
        pub_date = article.findtext(".//PubDate/Year", "")
        articles.append({
            "pmid": pmid,
            "title": title,
            "authors": ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else ""),
            "journal": journal,
            "year": pub_date,
            "abstract": abstract[:1500]  # 原始摘要，保留前1500字符
        })
    return articles


def search_on_google_scholar(query: str):
    """Google Scholar 检索占位函数"""
    return []


def search(
        query: str,
        method: Literal["pubmed", "google_scholar"] = "pubmed",
        max_results: int = 5
) -> List[Dict]:
    """统一的检索接口"""

    if method == "pubmed":
        return search_on_pubmed(query, max_results)
    elif method == "google_scholar":
        return search_on_google_scholar(query)
    else:
        raise ValueError("Invalid method. Choose 'pubmed' or 'google_scholar'.")


# --------------------- 智能体总结函数 -------------------- #
def summarize_results(query: str, articles: List[Dict]) -> str:
    """利用 LLM 对检索到的文献进行总结"""
    if not articles:
        return "未找到相关文献。"

    articles_text = "\n\n".join(
        f"文献{i+1}:\n标题: {art['title']}\n作者: {art['authors']}\n期刊: {art['journal']} ({art['year']})\n摘要: {art['abstract']}"
        for i, art in enumerate(articles)
    )
    prompt = f"""你是一位专业的科研助手。请根据以下检索到的文献，围绕研究主题"{query}"进行简要综述。
要求：
1. 概括这些文献共同关注的方向或方法。
2. 指出可能的研究缺口或未来方向。
3. 用中文撰写，结构清晰，300字左右。

文献信息：
{articles_text}"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是严谨的科研助手，请用中文回答。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"总结生成失败: {str(e)}"


# --------------------- 状态管理 -------------------- #
class TrackerState(rx.State):
    query: str = ""
    method: str = "pubmed"
    max_results: int = 5

    articles: List[Dict] = []
    summary: str = ""

    is_searching: bool = False
    is_summarizing: bool = False

    async def handle_search(self):
        if not self.query.strip():
            rx.toast.error("请输入检索关键词")
            return
        self.is_searching = True
        self.articles = []
        self.summary = ""
        yield
        try:
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                None, search, self.query, self.method, self.max_results
            )
            # 为每篇文章添加一个用于显示的短摘要字段
            for art in results:
                abstract = art.get("abstract", "")
                art["abstract_short"] = (abstract[:300] + "...") if len(abstract) > 300 else abstract
            self.articles = results
            if not results:
                rx.toast.warning("未检索到相关文献，请更换关键词重试")
        except Exception as e:
            rx.toast.error(f"检索失败: {str(e)}")
        finally:
            self.is_searching = False

    async def handle_summarize(self):
        if not self.articles:
            rx.toast.error("请先检索文献")
            return
        self.is_summarizing = True
        self.summary = ""
        yield
        try:
            loop = asyncio.get_running_loop()
            summary = await loop.run_in_executor(
                None, summarize_results, self.query, self.articles
            )
            self.summary = summary
        except Exception as e:
            self.summary = f"总结生成失败: {str(e)}"
        finally:
            self.is_summarizing = False

    def set_query(self, value: str):
        self.query = value

    def set_method(self, value: str):
        self.method = value


# --------------------- 页面组件 -------------------- #
def search_card():
    return rx.card(
            rx.vstack(
                rx.heading("Paper Search & Summary", size="5"),
                rx.hstack(
                    rx.input(
                        placeholder='e.g., "Bacillus subtilis"[tiab]',
                        value=TrackerState.query,
                        on_change=TrackerState.set_query,
                        width="100%"
                    ),
                    rx.select(
                        ["pubmed", "google_scholar"],
                        value=TrackerState.method,
                        on_change=TrackerState.set_method,
                        default_value="pubmed",
                    ),
                    rx.button(
                        "Search",
                        on_click=TrackerState.handle_search,
                        loading=TrackerState.is_searching,
                        color_scheme="blue"
                    ),
                    width="100%",
                    spacing="3",
                    align="center"
                ),
                width="100%",
            ),
            width="100%",
            padding="4"
    )


def results_display():
    return rx.cond(
        TrackerState.articles.length() > 0,
        rx.vstack(
            rx.heading(f"检索结果 ({TrackerState.articles.length()} 篇)", size="4"),
            rx.foreach(
                TrackerState.articles,
                lambda art, idx: rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.badge(art["pmid"], color_scheme="gray"),
                            rx.text(art["journal"], size="1", color="gray"),
                        ),
                        rx.link(art["title"], href=f"https://pubmed.ncbi.nlm.nih.gov/{art['pmid']}/", size="2", weight="bold"),
                        rx.text(art["authors"], size="1", color="gray"),
                        # 直接使用预先生成的短摘要字段，避免在渲染上下文中使用len/切片
                        rx.text(art["abstract_short"], size="1"),
                        spacing="1",
                    ),
                    width="100%",
                    padding="3"
                )
            ),
            rx.button(
                "生成文献总结",
                on_click=TrackerState.handle_summarize,
                loading=TrackerState.is_summarizing,
                color_scheme="green",
                width="100%"
            ),
            width="100%",
            spacing="3"
        ),
        rx.center(
            rx.text("尚未检索到文献，请输入关键词并点击检索", color="gray"),
            width="100%",
            padding="4em"
        )
    )


def summary_display():
    return rx.cond(
        TrackerState.summary != "",
        rx.card(
            rx.vstack(
                rx.heading("智能综述报告", size="4"),
                rx.markdown(TrackerState.summary),
                width="100%"
            ),
            width="100%",
            padding="4"
        )
    )


@rx.page('/tracker')
@web_structure
def tracker() -> rx.Component:
    return rx.container(
        rx.vstack(
            search_card(),
            results_display(),
            summary_display(),
            spacing="5",
            align_items="stretch",
            min_height="85vh",
        ),

        size="4",
        padding_top="5em",
        padding_bottom="2em",
        width='100%',
    )
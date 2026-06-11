import reflex as rx
from typing import List, Dict, Literal
import os
import math
import requests
from xml.etree import ElementTree
from collections import Counter
from openai import OpenAI

from ..templates import web_structure


# ==================== 配置 ==================== #
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-openai-api-key-here")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openai.cau.edu.cn/v1")
print(f"[OpenAI] Base URL: {OPENAI_BASE_URL}")
MODEL_NAME = "qwen3.6"
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

# ⚠️ 请务必将下面的邮箱替换为您的真实邮箱，否则 PubMed 会拒绝服务！
ENTREZ_EMAIL = "your-real-email@example.com"  # 修改这里！


# ==================== 检索函数 ==================== #
def search_on_pubmed(query: str, max_results: int = 5) -> List[Dict]:
    """使用 NCBI E-utilities 检索 PubMed"""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    articles = []

    try:
        # 搜索 PMID
        search_params = {
            "db": "pubmed", "term": query, "retmax": max_results,
            "retmode": "json", "sort": "relevance",
            "email": ENTREZ_EMAIL, "tool": "AlphaScholar",
        }
        search_resp = requests.get(f"{base_url}/esearch.fcgi", params=search_params)
        search_resp.raise_for_status()
        search_data = search_resp.json()
        id_list = search_data.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return articles

        # 获取详情
        fetch_params = {
            "db": "pubmed", "id": ",".join(id_list),
            "retmode": "xml", "email": ENTREZ_EMAIL, "tool": "AlphaScholar",
        }
        fetch_resp = requests.get(f"{base_url}/efetch.fcgi", params=fetch_params)
        fetch_resp.raise_for_status()
        root = ElementTree.fromstring(fetch_resp.text)

        for article_elem in root.findall(".//PubmedArticle"):
            medline = article_elem.find(".//MedlineCitation")
            if medline is None: continue
            pmid = medline.findtext("PMID", "")
            article_info = medline.find("Article")
            if article_info is None: continue

            title = article_info.findtext("ArticleTitle", "")
            abstract_parts = [
                "".join(e.itertext()) for e in article_info.findall(".//Abstract/AbstractText")
            ]
            abstract = " ".join(abstract_parts)

            authors_list = []
            for a in article_info.findall(".//AuthorList/Author"):
                last = a.findtext("LastName", "")
                fore = a.findtext("ForeName", "")
                if last: authors_list.append(f"{fore} {last}".strip())
            authors = ", ".join(authors_list[:3])
            if len(authors_list) > 3: authors += " et al."

            journal = article_info.findtext(".//Journal/Title", "")
            pub_date = ""
            date_comp = medline.find(".//DateCompleted")
            if date_comp is not None: pub_date = date_comp.findtext("Year", "")
            if not pub_date:
                pub_elem = article_info.find(".//Journal/JournalIssue/PubDate")
                if pub_elem is not None:
                    pub_date = pub_elem.findtext("Year", "") or pub_elem.findtext("MedlineDate", "")

            articles.append({
                "pmid": pmid, "title": title, "authors": authors,
                "journal": journal, "year": pub_date if pub_date else "未知",
                "abstract": abstract[:1500]
            })
    except Exception as e:
        print(f"[PubMed] 检索失败: {e}")
        raise RuntimeError(f"检索失败：{e}")

    return articles


def search_on_google_scholar(query: str) -> List[Dict]:
    return []


def search(query: str, method: Literal["pubmed", "google_scholar"] = "pubmed",
           max_results: int = 5) -> List[Dict]:
    if method == "pubmed":
        return search_on_pubmed(query, max_results)
    elif method == "google_scholar":
        return search_on_google_scholar(query)
    else:
        raise ValueError("无效检索方法")


# ==================== 总结函数 ==================== #
def summarize_results(query: str, articles: List[Dict]) -> str:
    if not articles:
        return "No relevant literature found."
    articles_text = "\n\n".join(
        f"Article {i+1}:\nTitle: {art['title']}\nAuthors: {art['authors']}\n"
        f"Journal: {art['journal']} ({art['year']})\nAbstract: {art['abstract']}"
        for i, art in enumerate(articles)
    )
    prompt = f"""你是一位专业的科研助手。请根据以下文献，围绕主题"{query}"进行综述。
要求：1. 概括共同方向或方法；2. 指出研究缺口或未来方向；3. 中文撰写，300字左右。

文献信息：
{articles_text}"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是严谨的科研助手，请用中文回答。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, max_tokens=600
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Failed to generate summary: {str(e)}"


# ==================== 状态管理（包含分页） ==================== #
class TrackerState(rx.State):
    query: str = ""
    method: str = "pubmed"
    max_results: int = 5

    articles: List[Dict] = []
    summary: str = ""

    stats_year: List[List] = []
    stats_journal: List[List] = []
    stats_total: int = 0

    is_searching: bool = False
    is_summarizing: bool = False

    # 分页
    current_page: int = 1
    page_size: int = 5

    @rx.var
    def total_pages(self) -> int:
        return max(1, math.ceil(len(self.articles) / self.page_size))

    @rx.var
    def paginated_articles(self) -> List[Dict]:
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return self.articles[start:end]

    @rx.var
    def page_numbers(self) -> List:
        total = self.total_pages
        current = self.current_page
        numbers = []
        if total <= 7:
            numbers = list(range(1, total + 1))
        else:
            numbers.append(1)
            if current > 3: numbers.append("...")
            start = max(2, current - 1)
            end = min(total - 1, current + 1)
            numbers.extend(range(start, end + 1))
            if current < total - 2: numbers.append("...")
            numbers.append(total)
        return numbers

    def go_to_page(self, page: int):
        if 1 <= page <= self.total_pages:
            self.current_page = page

    def _compute_stats(self):
        year_cnt = Counter()
        journal_cnt = Counter()
        for art in self.articles:
            year = art.get("year", "未知")
            if year: year_cnt[year] += 1
            journal = art.get("journal", "未知")
            if journal: journal_cnt[journal] += 1
        self.stats_year = [[yr, cnt] for yr, cnt in year_cnt.most_common()]
        self.stats_journal = [[j, cnt] for j, cnt in journal_cnt.most_common()]
        self.stats_total = len(self.articles)

    def handle_search(self):
        if not self.query.strip():
            rx.toast.error("请输入检索关键词")
            return

        self.is_searching = True
        self.articles = []
        self.summary = ""
        self.stats_year = []
        self.stats_journal = []
        self.stats_total = 0
        self.current_page = 1

        try:
            results = search(self.query, self.method, self.max_results)
            for art in results:
                abstract = art.get("abstract", "")
                art["abstract_short"] = (abstract[:300] + "...") if len(abstract) > 300 else abstract

            self.articles = results
            self._compute_stats()

            if not results:
                rx.toast.warning("未检索到相关文献，请更换关键词重试")
        except Exception as e:
            rx.toast.error(f"检索失败: {e}")
        finally:
            self.is_searching = False

    def handle_summarize(self):
        if not self.articles:
            rx.toast.error("请先检索文献")
            return

        self.is_summarizing = True
        self.summary = ""
        try:
            self.summary = summarize_results(self.query, self.articles)
        except Exception as e:
            self.summary = f"总结失败: {e}"
        finally:
            self.is_summarizing = False

    def set_query(self, value: str):
        self.query = value

    def set_method(self, value: str):
        self.method = value

    def set_max_results(self, value: list[int | float]):
        self.max_results = value[0]


# ==================== 页面组件 ==================== #
def search_card():
    return rx.card(
        rx.vstack(
            rx.heading("文献检索与智能总结", size="5"),
            rx.center(
                rx.vstack(
                    rx.heading("Query", size="2", color="gray"),
                    rx.input(
                        placeholder="输入研究关键词（如：bacillus subtilis[tiab]）",
                        value=TrackerState.query,
                        on_change=TrackerState.set_query,
                        width="100%",
                    ),
                    width="100%",
                ),
                rx.vstack(
                    rx.heading("Method", size="2", color="gray"),
                    rx.select(
                        ["pubmed", "google_scholar", "web_of_science"],
                        value=TrackerState.method,
                        on_change=TrackerState.set_method,
                        default_value="pubmed",
                    ),
                    width="50%",
                ),
                rx.vstack(
                    rx.heading("Max: ", TrackerState.max_results, size="2", color="gray"),
                    rx.slider(
                        default_value=TrackerState.max_results,
                        min=1, max=100,
                        on_change=TrackerState.set_max_results,
                        width="100%",
                    ),
                    width="50%",
                ),
                rx.button(
                    "检索",
                    on_click=TrackerState.handle_search,
                    loading=TrackerState.is_searching,
                    color_scheme="blue"
                ),
                width="100%",
                spacing="3",
                align="center"
            ),
        ),
        width="100%",
        padding="4"
    )


def results_display():
    return rx.cond(
        TrackerState.articles.length() > 0,
        rx.vstack(
            rx.heading(f"Search results ({TrackerState.articles.length()})", size="4"),
            rx.foreach(
                TrackerState.paginated_articles,
                lambda art, idx: rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.badge(art["pmid"], color_scheme="gray"),
                            rx.text(art["journal"], size="1", color="gray"),
                            rx.text(art["year"], size="1", color="gray"),
                        ),
                        rx.link(
                            art["title"],
                            href=f"https://pubmed.ncbi.nlm.nih.gov/{art['pmid']}/",
                            size="2", weight="bold",
                            is_external=True,
                        ),
                        rx.text(art["authors"], size="1", color="gray"),
                        rx.text(art["abstract_short"], size="1"),
                        spacing="1",
                    ),
                    width="100%",
                    padding="3"
                )
            ),
            # 分页导航（修复按钮文本）
            rx.cond(
                TrackerState.total_pages > 1,
                rx.hstack(
                    rx.button(
                        "‹",
                        on_click=lambda: TrackerState.go_to_page(TrackerState.current_page - 1),
                        disabled=TrackerState.current_page == 1,
                        size="1",
                    ),
                    rx.foreach(
                        TrackerState.page_numbers,
                        lambda page: rx.cond(
                            page == "...",
                            rx.text("...", size="1", color="gray"),
                            rx.button(
                                page,   # 直接使用 page，自动转为字符串显示
                                on_click=TrackerState.go_to_page(page),  # 点击时传递 page 的值
                                variant=rx.cond(
                                    TrackerState.current_page == page,
                                    "solid",
                                    "outline"
                                ),
                                size="1",
                            ),
                        ),
                    ),
                    rx.button(
                        "›",
                        on_click=lambda: TrackerState.go_to_page(TrackerState.current_page + 1),
                        disabled=TrackerState.current_page == TrackerState.total_pages,
                        size="1",
                    ),
                    spacing="2",
                    justify="center",
                    width="100%",
                ),
            ),
            rx.button(
                "Generate Summary",
                on_click=TrackerState.handle_summarize,
                loading=TrackerState.is_summarizing,
                color_scheme="green",
                width="100%"
            ),
            width="100%",
            spacing="3"
        ),
        rx.center(
            rx.text("No literature found. Please enter keywords and click search.", color="gray"),
            width="100%",
            padding="4em"
        )
    )


def stats_display():
    return rx.cond(
        TrackerState.articles.length() > 0,
        rx.card(
            rx.vstack(
                rx.heading("Reference Statistics", size="4"),
                rx.text(f"Total articles: {TrackerState.stats_total}"),
                rx.cond(
                    TrackerState.stats_year,
                    rx.vstack(
                        rx.text("📅 Year", weight="bold"),
                        rx.foreach(
                            TrackerState.stats_year,
                            lambda item: rx.text(f"{item[0]} Year: {item[1]} articles")
                        ),
                        spacing="1",
                    ),
                ),
                rx.cond(
                    TrackerState.stats_journal,
                    rx.vstack(
                        rx.text("📖 Journal", weight="bold"),
                        rx.foreach(
                            TrackerState.stats_journal,
                            lambda item: rx.text(f"{item[0]}: {item[1]} articles")
                        ),
                        spacing="1",
                    ),
                ),
                spacing="3",
            ),
            width="100%",
            padding="4"
        ),
    )


def summary_display():
    return rx.cond(
        TrackerState.summary != "",
        rx.card(
            rx.vstack(
                rx.heading("AI Summary", size="4"),
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
    return rx.box(
        rx.vstack(
            search_card(),
            results_display(),
            stats_display(),
            summary_display(),
            spacing="5",
            align_items="stretch",
            min_height="85vh",
        ),
        width="80%",
    )
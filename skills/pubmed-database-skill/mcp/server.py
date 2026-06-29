# skills/pubmed-database-skill/server.py
from fastmcp import FastMCP
from pymed import PubMed
import json
import os


mcp = FastMCP("pubmed-database-skill")


@mcp.tool()
def search_pubmed(query: str, max_results: int = 5) -> str:
    """在 PubMed 中检索生物医学文献。必须使用高级检索语法，如 [tiab] 等。"""

    pubmed = PubMed(tool="AlphaScholar", email=os.getenv("EMAIL", "user@example.com"))
    results = pubmed.query(query, max_results=max_results)
    articles = []
    for article in results:
        articles.append({
            "title": article.title,
            "authors": ", ".join([a['lastname'] for a in article.authors[:3]]),
            "date": str(article.publication_date),
            "abstract": (article.abstract or "")[:300],
            "doi": article.doi,
            "pmid": article.pubmed_id
        })
        
    return json.dumps(articles, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()  # 默认 stdio 传输
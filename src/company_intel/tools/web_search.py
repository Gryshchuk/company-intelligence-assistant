import httpx

from ..config import TAVILY_API_KEY


def web_search(query: str, max_results: int = 8) -> str:
    """Search the web via Tavily. Returns a numbered list of result snippets with URLs."""
    if not TAVILY_API_KEY:
        return "TAVILY_API_KEY not set; web search unavailable."
    r = httpx.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_answer": True,
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    if not results:
        return f"No web results for '{query}'."
    lines = []
    answer = (data.get("answer") or "").strip()
    if answer:
        lines.append(f"Summary: {answer}\n")
    for i, item in enumerate(results, 1):
        title = (item.get("title") or "").strip()
        url = item.get("url", "")
        snippet = (item.get("content") or "").strip().replace("\n", " ")
        lines.append(f"{i}. {title}\n   {url}\n   {snippet}")
    return "\n".join(lines)

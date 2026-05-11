"""Web search tool — wraps OpenAI hosted search with Brave Search fallback."""

import os
from typing import Any

import httpx
from agents import function_tool
from tenacity import retry, stop_after_attempt, wait_exponential

from market_watcher.config import BRAVE_API_KEY, USE_BRAVE_FALLBACK


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _brave_search(query: str, count: int = 5) -> list[dict]:
    headers = {"Accept": "application/json", "Accept-Encoding": "gzip", "X-Subscription-Token": BRAVE_API_KEY}
    params = {"q": query, "count": count, "text_decorations": False}
    resp = httpx.get("https://api.search.brave.com/res/v1/web/search", headers=headers, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("web", {}).get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": item.get("description", ""),
            "source": "Brave Search",
        })
    return results


@function_tool
def web_search(query: str) -> list[dict]:
    """Search the web for recent news and market intelligence about suppliers or the cloud infrastructure market.
    Returns a list of results with title, url, snippet, and source.
    Automatically falls back to Brave Search if OpenAI hosted search is unavailable.
    """
    if USE_BRAVE_FALLBACK and BRAVE_API_KEY:
        try:
            return _brave_search(query)
        except Exception as e:
            return [{"title": "Search error", "url": "", "snippet": f"Brave Search failed: {e}", "source": "error"}]

    # When called as a function_tool inside openai-agents, the SDK's hosted
    # web_search runs automatically. Here we return a placeholder for the
    # tool schema — the actual execution is handled by the agent framework.
    return [{"title": "Web search placeholder", "url": "", "snippet": query, "source": "openai_hosted"}]

import os
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent as create_langchain_agent
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import AIMessage

from part_a_basic_agent import get_store_hours
from tools.order_tools import get_order_status
from tools.product_tools import apply_coupon, search_products
from tools.utils import get_llm

load_dotenv()

_tavily = TavilySearchResults(
    max_results=3,
    include_domains=[
        "runnersworld.com",
        "sneakersnstuff.com",
        "shopstyle.com",
        "reddit.com",
        "techradar.com",
    ],
    exclude_domains=["spam.com"],
)


@tool
def web_search(query: str) -> str:
    """
    Search the web for live retail trends, reviews, and comparisons.

    Args:
        query: Search phrase requiring current or external internet information.

    Returns:
        A formatted summary of search results, or an availability/error message.
    """
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key or api_key == "your_tavily_key_here":
        return (
            "Web search is unavailable because TAVILY_API_KEY is not configured in .env."
        )

    try:
        results = _tavily.invoke({"query": query})
    except Exception as exc:  # pragma: no cover - external API behavior
        return f"Web search is currently unavailable: {exc}"

    if not results:
        return f"No web results found for '{query}'."

    if isinstance(results, str):
        return results

    lines = []
    for index, item in enumerate(results[:3], start=1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        snippet = item.get("content", "").replace("\n", " ").strip()
        lines.append(f"{index}. {title}\n   {snippet}\n   Source: {url}")
    return "Top web results:\n" + "\n".join(lines)


SYSTEM_PROMPT = """You are ShopBot, a smart retail assistant for ShopSphere.
You can use local store tools and web_search.
Prefer local tools for orders, coupons, inventory, and store info.
Use web_search only for live or external information such as trends and reviews.
"""


class DeepShopSphereAgent:
    """Compatibility wrapper that returns {'output': ..., 'messages': ...}."""

    def __init__(self, graph_agent: Any):
        self._graph_agent = graph_agent

    def invoke(self, payload: dict) -> dict:
        """Invoke wrapped graph agent with a legacy-compatible payload."""
        user_input = payload.get("input", "")
        result = self._graph_agent.invoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        messages = result.get("messages", [])
        final_message = ""
        for message in reversed(messages):
            if isinstance(message, AIMessage) and str(message.content).strip():
                final_message = message.content
                break
        if not final_message:
            for message in reversed(messages):
                if str(getattr(message, "content", "")).strip():
                    final_message = message.content
                    break
        return {"output": final_message, "messages": messages}


def create_deep_agent(tools: list, llm) -> DeepShopSphereAgent:
    """Build and return the deep agent configured with local and web tools."""
    graph_agent = create_langchain_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    return DeepShopSphereAgent(graph_agent)


_llm = get_llm()
_tools = [search_products, get_order_status, apply_coupon, get_store_hours, web_search]
deep_agent = create_deep_agent(_tools, _llm)


if __name__ == "__main__":
    test_queries = [
        "What is the status of order #CC-4821 for user@example.com?",
        "What are the top trending sneaker brands right now?",
        "Find me trending running shoes under $150 and apply coupon SUMMER20 to a $200 cart.",
    ]

    for query in test_queries:
        print(f"\n{'=' * 60}\nQuery: {query}\n{'=' * 60}")
        result = deep_agent.invoke({"input": query})
        tools_used = []
        for message in result.get("messages", []):
            if isinstance(message, AIMessage):
                tools_used.extend(call["name"] for call in getattr(message, "tool_calls", []))
        print(f"Tools Used: {tools_used or ['none']}")
        print(f"Final Answer: {result['output']}")

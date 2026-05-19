from typing import Any

from langchain.agents import create_agent as create_langchain_agent
from langchain_core.messages import AIMessage

from tools.order_tools import cancel_order, get_order_status, process_return, track_shipment
from tools.product_tools import (
    apply_coupon,
    check_inventory,
    get_product_details,
    get_recommendations,
    search_products,
)
from tools.input_guard import check_user_input
from tools.utils import get_llm, load_prompt

_llm = get_llm()


class DomainAgent:
    """Wrapper for LangChain graph agents with invoke({'input': ...}) support."""

    def __init__(self, graph_agent: Any):
        self._graph_agent = graph_agent

    def invoke(self, payload: dict) -> dict:
        """Invoke the wrapped graph agent and normalize output format."""
        user_input = payload.get("input", "")
        guard = check_user_input(user_input)
        if not guard.allowed:
            return {"output": guard.message, "messages": []}
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


def make_agent(tools: list, domain: str) -> DomainAgent:
    """Create and return a domain-specialized agent for orchestration."""
    system_prompt = load_prompt("part_c_domain", domain=domain)
    graph_agent = create_langchain_agent(
        model=_llm,
        tools=tools,
        system_prompt=system_prompt,
    )
    return DomainAgent(graph_agent)


product_agent = make_agent(
    tools=[
        search_products,
        get_product_details,
        check_inventory,
        get_recommendations,
        apply_coupon,
    ],
    domain="products, inventory, recommendations, and promotions",
)

order_agent = make_agent(
    tools=[get_order_status, cancel_order, track_shipment, process_return],
    domain="order management, cancellations, shipment tracking, and returns",
)


ORDER_KEYWORDS = [
    "order",
    "status",
    "cancel",
    "return",
    "refund",
    "shipment",
    "tracking",
    "delivered",
    "dispatch",
    "track",
]


def keyword_router(query: str) -> str:
    """
    Route a query to either the product or order specialist.

    Args:
        query: User question that needs domain classification.

    Returns:
        The route label 'order' when order keywords exist, otherwise 'product'.
    """
    query_lower = query.lower()
    if any(keyword in query_lower for keyword in ORDER_KEYWORDS):
        return "order"
    return "product"


def orchestrate(query: str) -> str:
    """
    Dispatch a query to the routed specialist agent and return the response text.

    Args:
        query: User query string to route and answer.

    Returns:
        Final assistant response from the selected specialist agent.
    """
    route = keyword_router(query)
    print(f"\n[Router] '{query[:50]}...' -> routed to: {route.upper()} AGENT")

    if route == "order":
        result = order_agent.invoke({"input": query})
    else:
        result = product_agent.invoke({"input": query})

    return result["output"]


if __name__ == "__main__":
    test_queries = [
        "Show me running shoes under $130.",
        "What is the status of order #CC-9910 for john@example.com?",
        "I want to return items from order #CC-5001.",
        "Check if SKU NK-001 is available in Bengaluru.",
        "Show me Dell laptops under $700.",
    ]

    print("\n" + "=" * 60)
    print("MULTI-AGENT ROUTING TEST")
    print("=" * 60)

    for query in test_queries:
        print(f"\nQuery: {query}")
        answer = orchestrate(query)
        print(f"Answer: {answer}")

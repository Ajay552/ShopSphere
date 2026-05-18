from typing import Any

from langchain.agents import create_agent as create_langchain_agent
from langchain_core.messages import AIMessage
from langchain.tools import tool

from tools.order_tools import get_order_status
from tools.product_tools import apply_coupon, search_products
from tools.utils import get_llm, load_data


@tool
def get_store_hours(location: str) -> str:
    """
    Return operating hours for a ShopSphere store location.

    Args:
        location: City or store location name, such as Bengaluru.

    Returns:
        Weekday and weekend operating hours, or a not-found message.
    """
    store_hours = load_data("store_hours.json")
    info = store_hours.get(location)
    if info is None:
        available_locations = ", ".join(store_hours.keys())
        return (
            f"No store found for '{location}'. Available locations: {available_locations}"
        )

    return (
        f"ShopSphere {location}:\n"
        f"Mon-Fri: {info['weekday']}\n"
        f"Sat-Sun: {info['weekend']}"
    )


SYSTEM_PROMPT = """You are ShopBot, a helpful retail assistant for ShopSphere.
Use the available tools to answer customer queries accurately.
Always use tools for product search, order status, coupons, and store hours.
If a tool returns no results, say so clearly and do not guess.
"""


class ShopSphereAgent:
    """Lightweight compatibility wrapper that exposes invoke({'input': ...})."""

    def __init__(self, graph_agent: Any):
        self._graph_agent = graph_agent

    def invoke(self, payload: dict) -> dict:
        """Invoke the wrapped agent graph and normalize output shape."""
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


def create_agent(tools: list, llm) -> ShopSphereAgent:
    """Build and return a configured LangChain tool-calling agent."""
    graph_agent = create_langchain_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    return ShopSphereAgent(graph_agent)


_llm = get_llm()
_tools = [search_products, get_order_status, apply_coupon, get_store_hours]
agent = create_agent(_tools, _llm)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TOOL METADATA INSPECTION")
    print("=" * 60)
    for tool_obj in _tools:
        print(f"\nTool Name   : {tool_obj.name}")
        print(f"Description : {tool_obj.description}")
        schema = (
            tool_obj.args_schema.model_json_schema()
            if hasattr(tool_obj.args_schema, "model_json_schema")
            else tool_obj.args_schema.schema()
        )
        print("Args Schema :")
        for field, props in schema.get("properties", {}).items():
            field_type = props.get("type", "unknown")
            description = props.get("description", "-")
            print(f"  - {field} ({field_type}): {description}")

    test_queries = [
        "Find me running shoes under $150 in the shoes category.",
        "What is the status of order #CC-4821 for user@example.com?",
        "Apply coupon SUMMER20 to my $200 cart.",
    ]

    print("\n" + "=" * 60)
    print("AGENT TEST QUERIES")
    print("=" * 60)
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 40)
        result = agent.invoke({"input": query})
        tools_used = []
        for message in result.get("messages", []):
            if isinstance(message, AIMessage):
                tools_used.extend(call["name"] for call in getattr(message, "tool_calls", []))
        print(f"Tools Used: {tools_used or ['none']}")
        print(f"Final Answer: {result['output']}")

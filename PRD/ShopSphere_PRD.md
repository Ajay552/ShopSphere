# ShopSphere — Intelligent Retail Assistant Platform
### Product Requirements Document (Assignment)

---

## Table of Contents

1. [Overview](#overview)
2. [Tech Stack](#tech-stack)
3. [Dummy Data — JSON Database](#dummy-data--json-database)
4. [Project Structure](#project-structure)
5. [Streamlit UI](#streamlit-ui)
6. [Part A — Basic Agent](#part-a--basic-agent)
7. [Part B — Deep Agent with Tavily Search](#part-b--deep-agent-with-tavily-search)
8. [Part C — Multi-Agent Orchestration](#part-c--multi-agent-orchestration)
9. [Deliverables Checklist](#deliverables-checklist)
10. [Reflections](#reflections)

---

## Overview

**ShopSphere** is a conversational retail assistant built progressively across three parts:

| Part | Focus | Complexity |
|------|-------|------------|
| A | Basic tool-equipped ReAct agent | Beginner–Intermediate |
| B | Deep agent with live web search (Tavily) | Intermediate |
| C | Multi-agent system with keyword router | Intermediate |

**Goal:** Understand how LangChain agents reason, select tools, chain actions, and scale into multi-agent architectures.

---

## Tech Stack

| Component | Choice | Notes |
|-----------|--------|-------|
| LLM | `gemma4:e4b` via Ollama | Running locally, no API key needed |
| Agent Framework | LangChain | `create_react_agent` or `AgentExecutor` |
| Web Search | Tavily API | Requires `TAVILY_API_KEY` in `.env` |
| UI | Streamlit | Simple chat interface; React planned for later |
| Data Layer | JSON files | Flat JSON files act as a mock database |
| Language | Python 3.10+ | |
| Environment | `python-dotenv` | For loading Tavily key from `.env` |

### Setup

```bash
pip install langchain langchain-community langchain-ollama tavily-python python-dotenv streamlit
```

**.env file:**
```
TAVILY_API_KEY=your_tavily_key_here
```

**Ollama setup:**
```bash
ollama pull gemma4:e4b   # pull the model
ollama serve             # make sure Ollama is running
```

---

## Dummy Data — JSON Database

All tools query **local JSON files** that act as a mock database. No real database or external product API is used. This keeps the setup simple and self-contained.

### File: `data/products.json`

```json
[
  {
    "sku": "RS-001",
    "name": "Running Shoe X",
    "category": "shoes",
    "price": 129.99,
    "brand": "SwiftStep",
    "in_stock": true,
    "locations": ["Bengaluru", "Mumbai"]
  },
  {
    "sku": "TB-002",
    "name": "Trail Blazer Pro",
    "category": "shoes",
    "price": 144.99,
    "brand": "TerraTread",
    "in_stock": true,
    "locations": ["Bengaluru"]
  },
  {
    "sku": "WL-003",
    "name": "Wireless Headphones Z",
    "category": "electronics",
    "price": 89.99,
    "brand": "SoundWave",
    "in_stock": false,
    "locations": []
  },
  {
    "sku": "YG-004",
    "name": "Yoga Mat Premium",
    "category": "fitness",
    "price": 49.99,
    "brand": "FlexFit",
    "in_stock": true,
    "locations": ["Bengaluru", "Delhi", "Chennai"]
  }
]
```

### File: `data/orders.json`

```json
[
  {
    "order_id": "CC-4821",
    "customer_email": "user@example.com",
    "status": "Shipped",
    "items": ["RS-001"],
    "total": 129.99,
    "tracking_number": "TRK-99821",
    "estimated_delivery": "2 days"
  },
  {
    "order_id": "CC-9910",
    "customer_email": "john@example.com",
    "status": "Processing",
    "items": ["WL-003", "YG-004"],
    "total": 139.98,
    "tracking_number": null,
    "estimated_delivery": "5 days"
  },
  {
    "order_id": "CC-5001",
    "customer_email": "sara@example.com",
    "status": "Delivered",
    "items": ["TB-002"],
    "total": 144.99,
    "tracking_number": "TRK-55512",
    "estimated_delivery": "Delivered"
  }
]
```

### File: `data/coupons.json`

```json
[
  { "code": "SUMMER20", "discount_percent": 20, "active": true },
  { "code": "SAVE10",   "discount_percent": 10, "active": true },
  { "code": "EXPIRED5", "discount_percent": 5,  "active": false }
]
```

### File: `data/store_hours.json`

```json
{
  "Bengaluru":      { "weekday": "9:00 AM – 9:00 PM", "weekend": "10:00 AM – 8:00 PM" },
  "Mumbai-Central": { "weekday": "10:00 AM – 9:00 PM", "weekend": "10:00 AM – 7:00 PM" },
  "Delhi":          { "weekday": "9:00 AM – 8:00 PM",  "weekend": "10:00 AM – 6:00 PM" }
}
```

### How Tools Use the JSON Data

Each tool loads its relevant JSON file and filters/searches it at runtime. Example pattern:

```python
import json

def load_data(filename: str):
    with open(f"data/{filename}", "r") as f:
        return json.load(f)
```

This replaces the hardcoded string returns from the original stub tools. Every query the agent makes — product searches, order lookups, coupon checks — reads from these JSON files, making the behaviour consistent and testable across all three parts.

---

## Project Structure

```
shopsphere/
├── .env
├── app.py                     # Streamlit UI entry point
├── part_a_basic_agent.py
├── part_b_deep_agent.py
├── part_c_multi_agent.py
├── data/
│   ├── products.json
│   ├── orders.json
│   ├── coupons.json
│   └── store_hours.json
└── tools/
    ├── __init__.py
    ├── product_tools.py
    ├── order_tools.py
    └── search_tools.py
```

---

## Streamlit UI

> **Current:** Streamlit (simple, fast to build)
> **Planned:** React frontend (future iteration)

The Streamlit app (`app.py`) provides a basic chat interface where users can type queries and see agent responses. It wraps the Part C multi-agent orchestrator so queries are automatically routed to the right agent.

### Features

| Feature | Details |
|---------|---------|
| Chat input | Single text box for user queries |
| Agent selector | Sidebar radio: Auto (router) / Product Agent / Order Agent |
| Response display | Agent's final answer shown in chat bubble |
| Agent trace toggle | Expandable section showing `Thought → Action → Observation` |
| Part selector | Sidebar to switch between Part A / B / C agents |

### `app.py` — Basic Structure

```python
import streamlit as st
from part_c_multi_agent import orchestrate
from part_b_deep_agent import deep_agent

st.set_page_config(page_title="ShopSphere Assistant", page_icon="🛍️")
st.title("🛍️ ShopSphere — Retail Assistant")

# Sidebar controls
st.sidebar.header("Settings")
part = st.sidebar.radio("Agent Mode", ["Part A — Basic", "Part B — Deep (Web)", "Part C — Multi-Agent"])

# Chat history stored in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# User input
if user_input := st.chat_input("Ask ShopBot anything..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Route to correct agent based on selected mode
    with st.chat_message("assistant"):
        with st.spinner("ShopBot is thinking..."):
            if part == "Part C — Multi-Agent":
                response = orchestrate(user_input)
            elif part == "Part B — Deep (Web)":
                result = deep_agent.invoke({"input": user_input})
                response = result["output"]
            else:
                # Part A basic agent
                from part_a_basic_agent import agent as basic_agent
                result = basic_agent.invoke({"input": user_input})
                response = result["output"]

        st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
```

### Running the UI

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501` in your browser.

> **Note on React:** The Streamlit UI is intentionally minimal for this assignment. A React frontend using the same agent backend (exposed via a FastAPI endpoint) is planned as a future upgrade.

---

## Part A — Basic Agent

### A.1 — Define 4 Tool Functions

Define each tool using the `@tool` decorator from LangChain. Each tool must have a complete docstring with `Args` and `Returns` sections so LangChain can auto-generate its JSON schema.

**File:** `tools/product_tools.py` and `tools/order_tools.py`

> All tools load data from the JSON files in `data/`. The pattern is: load the file → filter/search → return a formatted string result.

```python
import json
from langchain.tools import tool

def load_data(filename: str):
    with open(f"data/{filename}", "r") as f:
        return json.load(f)


@tool
def search_products(query: str, category: str, max_price: float) -> str:
    """
    Search for products in the ShopSphere catalog.

    Args:
        query (str): The search keyword or product name.
        category (str): Product category (e.g., 'shoes', 'electronics').
        max_price (float): Maximum acceptable price in USD.

    Returns:
        str: A list of matching products with name, price, and SKU.
    """
    products = load_data("products.json")
    results = [
        p for p in products
        if (query.lower() in p["name"].lower() or query.lower() in p["brand"].lower())
        and p["category"].lower() == category.lower()
        and p["price"] <= max_price
        and p["in_stock"]
    ]
    if not results:
        return f"No products found for '{query}' in '{category}' under ${max_price}."
    lines = [f"{i+1}. {p['name']} — ${p['price']} (SKU: {p['sku']})" for i, p in enumerate(results)]
    return f"Found {len(results)} product(s):\n" + "\n".join(lines)


@tool
def get_order_status(order_id: str, customer_email: str) -> str:
    """
    Retrieve the current status of a customer order.

    Args:
        order_id (str): The unique order identifier (e.g., 'CC-4821').
        customer_email (str): Email address associated with the order.

    Returns:
        str: Order status including shipping state and estimated delivery.
    """
    orders = load_data("orders.json")
    order = next(
        (o for o in orders if o["order_id"] == order_id and o["customer_email"] == customer_email),
        None
    )
    if not order:
        return f"No order found for ID '{order_id}' with email '{customer_email}'."
    return (
        f"Order {order['order_id']}:\n"
        f"Status: {order['status']}\n"
        f"Tracking: {order['tracking_number'] or 'Not yet assigned'}\n"
        f"Estimated Delivery: {order['estimated_delivery']}"
    )


@tool
def apply_coupon(code: str, cart_total: float) -> str:
    """
    Apply a discount coupon to a shopping cart.

    Args:
        code (str): The coupon code to apply (e.g., 'SUMMER20').
        cart_total (float): The current cart total in USD before discount.

    Returns:
        str: Updated cart total after discount, or an error if code is invalid.
    """
    coupons = load_data("coupons.json")
    coupon = next((c for c in coupons if c["code"] == code and c["active"]), None)
    if not coupon:
        return f"Coupon '{code}' is invalid or expired."
    discount = cart_total * (coupon["discount_percent"] / 100)
    new_total = cart_total - discount
    return f"Coupon '{code}' applied! Discount: ${discount:.2f}. New total: ${new_total:.2f}"


@tool
def get_store_hours(location: str) -> str:
    """
    Get store operating hours for a given ShopSphere location.

    Args:
        location (str): City or store name (e.g., 'Bengaluru', 'Mumbai-Central').

    Returns:
        str: Store hours for weekdays and weekends.
    """
    hours = load_data("store_hours.json")
    info = hours.get(location)
    if not info:
        return f"No store found for location '{location}'."
    return (
        f"ShopSphere {location}:\n"
        f"Mon–Fri: {info['weekday']}\n"
        f"Sat–Sun: {info['weekend']}"
    )
```

---

### A.2 — Inspect Tool Metadata Programmatically

Print each tool's name, description, and argument schema to understand how LangChain parses docstrings and type hints.

```python
tools = [search_products, get_order_status, apply_coupon, get_store_hours]

for tool in tools:
    print(f"\n{'='*50}")
    print(f"Tool Name   : {tool.name}")
    print(f"Description : {tool.description}")
    print(f"Args Schema :")
    schema = tool.args_schema.schema()
    for field, props in schema.get("properties", {}).items():
        ftype = props.get("type", "unknown")
        desc  = props.get("description", "—")
        print(f"  - {field} ({ftype}): {desc}")
```

**Expected Output (example):**
```
==================================================
Tool Name   : search_products
Description : Search for products in the ShopSphere catalog.
Args Schema :
  - query (string): The search keyword or product name.
  - category (string): Product category (e.g., 'shoes', 'electronics').
  - max_price (number): Maximum acceptable price in USD.
```

---

### A.3 — Create the ReAct Agent

**File:** `part_a_basic_agent.py`

```python
from langchain_ollama import ChatOllama
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from tools.product_tools import search_products, get_order_status, apply_coupon, get_store_hours

def create_agent(tools, llm):
    """Build and return a ReAct AgentExecutor."""

    system_prompt = PromptTemplate.from_template("""
You are ShopBot, a helpful retail assistant for ShopSphere.
Use the available tools to answer customer queries accurately.
Always reason step-by-step before calling a tool.

Tools available:
{tools}

Tool names: {tool_names}

Use this format:
Question: the input question
Thought: your reasoning
Action: tool name
Action Input: tool input
Observation: tool result
... (repeat as needed)
Thought: I now know the final answer
Final Answer: your response to the customer

Question: {input}
{agent_scratchpad}
""")

    agent = create_react_agent(llm=llm, tools=tools, prompt=system_prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=5,
        handle_parsing_errors=True,
        verbose=True  # shows full trace
    )


if __name__ == "__main__":
    llm = ChatOllama(model="gemma4:e4b", temperature=0)
    tools = [search_products, get_order_status, apply_coupon, get_store_hours]
    agent = create_agent(tools, llm)

    queries = [
        "Find me running shoes under $150 in the sports category.",
        "What is the status of order #CC-4821 for user@example.com?",
        "Apply coupon SUMMER20 to my cart of $200."
    ]

    for q in queries:
        print(f"\n{'='*60}\nQuery: {q}\n{'='*60}")
        result = agent.invoke({"input": q})
        print("Final Answer:", result["output"])
```

---

### A.4 — Expected Test Traces

| Query | Expected Tool Used | Expected Reasoning |
|-------|-------------------|--------------------|
| "Find running shoes under $150" | `search_products` | Extracts query, category, price from input |
| "Status of order #CC-4821" | `get_order_status` | Parses order ID and email from query |
| "Apply SUMMER20 to $200 cart" | `apply_coupon` | Parses coupon code and cart total |

The `verbose=True` flag in `AgentExecutor` will print the full `Thought → Action → Observation` trace.

---

## Part B — Deep Agent with Tavily Search

### B.1 — Integrate Tavily as 5th Tool

**File:** `part_b_deep_agent.py`

```python
import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_ollama import ChatOllama
from langchain.agents import create_react_agent, AgentExecutor
from tools.product_tools import search_products, get_order_status, apply_coupon, get_store_hours

load_dotenv()  # loads TAVILY_API_KEY from .env

tavily_tool = TavilySearchResults(
    max_results=3,
    include_domains=["shopstyle.com", "sneakersnstuff.com", "runnersworld.com", "reddit.com"],
    exclude_domains=["spam-site.com"]
)
tavily_tool.name = "web_search"
tavily_tool.description = (
    "Search the internet for real-time retail trends, product reviews, "
    "brand comparisons, or any information not available in local tools."
)
```

> **Why Tavily vs. static tools?**
> Local tools return hardcoded/DB data — they're fast but fixed.
> Tavily fetches live web results, so the agent can answer questions about trending products,
> current prices, or recent news that don't exist in the local database.

---

### B.2 — Test Query 1: Local Only

```python
query = "What is the status of order #CC-4821 for user@example.com?"
```

**Expected behavior:** Agent should pick `get_order_status`, NOT `web_search`.  
The trace should show the agent reasoning that this query requires an order ID lookup, which is a local tool responsibility.

---

### B.3 — Test Query 2: Internet Only

```python
query = "What are the top trending sneaker brands right now?"
```

**Expected behavior:** Agent uses `web_search` (Tavily).  
The trace should show retrieved web snippets and a synthesized answer citing brand names from the results.

---

### B.4 — Test Query 3: Compound Multi-Tool

```python
query = "Find me trending running shoes under $150 and apply coupon SUMMER20 to a $200 cart."
```

**Expected tool chain:**
```
web_search (trending shoes) → search_products (filter by price) → apply_coupon (SUMMER20, $200)
```

This tests multi-hop reasoning: the agent must plan all 3 steps before starting.

---

### B.5 — Reflection (200 words)

*Write this in your own words in the submission. Use the points below as guidance:*

- **Local tools** are preferred when the data is structured and deterministic (order IDs, inventory, coupons). They're fast, reliable, and don't cost extra API credits.
- **Web search** is preferred when the query needs current or external information (trends, reviews, competitor prices) that your local database doesn't cover.
- **Risks of internet access:** web results can be noisy, outdated, or from unreliable sources. The LLM may hallucinate by blending real search snippets with fabricated details. Citations should be logged and validated.
- **Tool-selection policy ideas:** add a simple classifier or keyword check before calling the agent to pre-route; alternatively, add a tool description that explicitly states "only use this for live/trending queries" so the LLM selects appropriately.

---

## Part C — Multi-Agent Orchestration

### C.1 — Define Two Specialized Agents

**File:** `part_c_multi_agent.py`

```python
from langchain_ollama import ChatOllama
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate

llm = ChatOllama(model="gemma4:e4b", temperature=0)

# --- Product Agent Tools ---
from tools.product_tools import (
    search_products, get_product_details,
    check_inventory, get_recommendations, apply_coupon
)

# --- Order Agent Tools ---
from tools.order_tools import (
    get_order_status, cancel_order,
    track_shipment, process_return
)


def make_agent(tools, system_role: str):
    prompt = PromptTemplate.from_template(f"""
You are a ShopSphere assistant specializing in {system_role}.
Only use the tools available to you. Do not attempt tasks outside your domain.

Tools: {{tools}}
Tool names: {{tool_names}}

Question: {{input}}
{{agent_scratchpad}}
""")
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, max_iterations=5,
                         handle_parsing_errors=True, verbose=True)


product_agent = make_agent(
    tools=[search_products, get_product_details, check_inventory, get_recommendations, apply_coupon],
    system_role="products, inventory, and promotions"
)

order_agent = make_agent(
    tools=[get_order_status, cancel_order, track_shipment, process_return],
    system_role="order management, shipments, and returns"
)
```

> **Note:** You'll need to define stub implementations for `get_product_details`, `check_inventory`,
> `get_recommendations`, `cancel_order`, `track_shipment`, and `process_return` — same pattern as Part A tools.

---

### C.2 — Keyword Router

```python
def keyword_router(query: str) -> str:
    """
    Route query to 'product' or 'order' agent based on keywords.
    Defaults to 'product' for ambiguous queries.
    """
    query_lower = query.lower()

    order_keywords = [
        "order", "status", "cancel", "return", "refund",
        "shipment", "tracking", "delivered", "dispatch"
    ]

    if any(kw in query_lower for kw in order_keywords):
        return "order"

    return "product"  # default fallback
```

---

### C.3 — Orchestrator

```python
def orchestrate(query: str) -> str:
    """Route query to the correct agent and return the response."""
    route = keyword_router(query)
    print(f"\n[Router] Query routed to: {route.upper()} AGENT")

    if route == "order":
        result = order_agent.invoke({"input": query})
    else:
        result = product_agent.invoke({"input": query})

    return result["output"]
```

---

### C.4 — Test Queries

```python
test_queries = [
    "Show me running shoes under $100.",                         # → product
    "What is the status of order #CC-9910?",                    # → order
    "I want to return items from order #CC-5001.",              # → order
    "Check inventory for SKU TB-002 and cancel order #CC-123.", # → order (edge case)
    "I need something comfortable.",                            # → product (ambiguous)
]

for q in test_queries:
    print(f"\n{'='*60}\nQuery: {q}")
    answer = orchestrate(q)
    print(f"Answer: {answer}")
```

**Expected Routing Table:**

| Query | Router Decision | Agent Used |
|-------|----------------|------------|
| "running shoes under $100" | `product` | Product Agent |
| "status of order #CC-9910" | `order` | Order Agent |
| "return items from order" | `order` | Order Agent |
| "inventory + cancel order" | `order` | Order Agent (keyword wins) |
| "something comfortable" | `product` (default) | Product Agent |

---

### C.5 — Reflection (250 words)

*Write this in your own words. Use the points below as guidance:*

**Advantages of specialization over monolith:**
- Each agent has a focused system prompt, so the LLM reasons better within its domain.
- Fewer tools per agent = less confusion during tool selection.
- Easier to debug — if orders are broken, only the order agent needs fixing.
- Agents can be scaled or updated independently.

**Failure modes of routing:**
- Keyword-based routing is brittle — "I want to cancel my gym membership" might wrongly trigger the order agent.
- Ambiguous queries (e.g., "help me with my recent purchase") may land in the wrong agent.
- If the query needs both domains (inventory check + cancel order), a single-agent route drops half the task.

**Evolving to LangGraph Supervisor Pattern:**
- A **supervisor node** replaces the keyword router. It's an LLM itself that reads the full query and decides which sub-agent (or combination) should handle it.
- LangGraph lets agents pass results to each other through a shared state graph — solving the cross-domain query problem.
- The supervisor can also handle retries, fallbacks, and partial responses more gracefully than a simple `if/else` router.
- This is the production-grade evolution: keyword router → LLM router → LangGraph supervisor with memory and state.

---

## Deliverables Checklist

### Data Layer
- [ ] `data/products.json` with 4+ products
- [ ] `data/orders.json` with 3+ orders
- [ ] `data/coupons.json` with active and inactive coupons
- [ ] `data/store_hours.json` with 3+ locations
- [ ] `load_data()` utility used consistently across all tools

### Streamlit UI
- [ ] `app.py` with chat input and response display
- [ ] Sidebar to switch between Part A / B / C agent modes
- [ ] Agent trace viewable (expandable section or `verbose` output in terminal)
- [ ] App runs cleanly with `streamlit run app.py`

### Part A
- [ ] 4 `@tool` functions reading from JSON files
- [ ] Metadata inspection printout
- [ ] `create_agent()` implementation
- [ ] 3 test query traces with tool calls visible

### Part B
- [ ] Tavily integrated as 5th tool
- [ ] Query 1 trace (local only — order status)
- [ ] Query 2 trace (web only — trending sneakers)
- [ ] Query 3 trace (compound chain)
- [ ] 200-word reflection

### Part C
- [ ] `product_agent` with 5 tools
- [ ] `order_agent` with 4 tools
- [ ] `keyword_router()` with edge case handling
- [ ] `orchestrate()` function with logging
- [ ] 5+ test queries with routing decisions shown
- [ ] 250-word reflection

---

## Quick Reference — Key Concepts Used

| Concept | Used In | Purpose |
|---------|---------|---------|
| `@tool` decorator | All parts | Converts Python functions into LangChain tools |
| `args_schema` | A.2 | Auto-generated JSON schema from type hints + docstrings |
| `create_react_agent` | A.3, B, C | Builds ReAct reasoning loop |
| `AgentExecutor` | A.3, B, C | Runs the agent with iteration/error controls |
| `TavilySearchResults` | Part B | Live web search integration |
| `ChatOllama` | All parts | Local LLM via Ollama (no API key needed) |
| `verbose=True` | All parts | Prints full Thought→Action→Observation trace |
| JSON files | All parts | Mock database for products, orders, coupons, store hours |
| `load_data()` helper | All tools | Centralised JSON file loader used by every tool |
| Streamlit | `app.py` | Chat UI for interacting with agents in the browser |

---

*ShopSphere Assignment PRD — Basic to Intermediate Level*
*LLM: gemma4:e4b (Ollama local) | Web Search: Tavily API | UI: Streamlit | Data: JSON mock files*
# ShopSphere — Implementation Plan
### Companion to: `PRD/ShopSphere_PRD.md`

---

## Table of Contents

1. [Build Order Overview](#build-order-overview)
2. [Dependency Graph](#dependency-graph)
3. [Phase 0 — Project Scaffold & Environment](#phase-0--project-scaffold--environment)
4. [Phase 1 — Data Layer (JSON Files)](#phase-1--data-layer-json-files)
5. [Phase 2 — Shared Utilities](#phase-2--shared-utilities)
6. [Phase 3 — Part A: Tool Definitions](#phase-3--part-a-tool-definitions)
7. [Phase 4 — Part A: Basic Agent](#phase-4--part-a-basic-agent)
8. [Phase 5 — Part B: Deep Agent with Tavily](#phase-5--part-b-deep-agent-with-tavily)
9. [Phase 6 — Part C: Multi-Agent Orchestration](#phase-6--part-c-multi-agent-orchestration)
10. [Phase 7 — Streamlit UI](#phase-7--streamlit-ui)
11. [Verification Checklist](#verification-checklist)
12. [Known Gotchas & Fixes](#known-gotchas--fixes)
13. [File-by-File Spec Summary](#file-by-file-spec-summary)

---

## Build Order Overview

```
Phase 0  →  Scaffold folders, install deps, create .env
Phase 1  →  Create all 4 JSON data files
Phase 2  →  Create shared utils (load_data, LLM init, prompt template)
Phase 3  →  Build tools/product_tools.py  +  tools/order_tools.py
Phase 4  →  Build part_a_basic_agent.py  (imports from Phase 3)
Phase 5  →  Build part_b_deep_agent.py   (imports from Phase 3 + adds Tavily)
Phase 6  →  Build part_c_multi_agent.py  (imports from Phase 3, reuses agent factory)
Phase 7  →  Build app.py Streamlit UI    (imports from Phase 4, 5, 6)
```

**Rule:** Each phase depends only on phases before it. Build and test sequentially.

---

## Dependency Graph

```
data/*.json
    └── tools/utils.py (load_data helper)
            ├── tools/product_tools.py
            │       ├── part_a_basic_agent.py
            │       ├── part_b_deep_agent.py
            │       └── part_c_multi_agent.py
            └── tools/order_tools.py
                    ├── part_a_basic_agent.py  (get_order_status only)
                    ├── part_b_deep_agent.py   (get_order_status only)
                    └── part_c_multi_agent.py  (all 4 order tools)

part_a_basic_agent.py  ──┐
part_b_deep_agent.py   ──┼──► app.py (Streamlit)
part_c_multi_agent.py  ──┘
```

---

## Phase 0 — Project Scaffold & Environment

### 0.1 Create folder structure

```bash
mkdir shopsphere
cd shopsphere
mkdir data tools
touch tools/__init__.py
touch tools/utils.py
touch tools/product_tools.py
touch tools/order_tools.py
touch part_a_basic_agent.py
touch part_b_deep_agent.py
touch part_c_multi_agent.py
touch app.py
touch .env
```

### 0.2 Install dependencies

```bash
pip install langchain langchain-community langchain-ollama \
            tavily-python python-dotenv streamlit
```

### 0.3 Create `.env`

```
TAVILY_API_KEY=your_tavily_key_here
```

### 0.4 Verify Ollama is running with correct model

```bash
ollama list          # confirm gemma4:e4b is present
ollama serve         # start server if not already running
```

Test the model responds:
```bash
ollama run gemma4:e4b "Say hello"
```

### 0.5 Smoke-test LangChain + Ollama connection

Create a throwaway `test_llm.py` and run it — delete after:

```python
from langchain_ollama import ChatOllama
llm = ChatOllama(model="gemma4:e4b", temperature=0)
print(llm.invoke("Say: LangChain connected"))
```

```bash
python test_llm.py
# Expected: AIMessage with "LangChain connected" or similar
```

✅ **Phase 0 done when:** folder exists, deps installed, Ollama responds.

---

## Phase 1 — Data Layer (JSON Files)

Create all four files inside `data/`. These are the mock database — every tool reads from here.

### 1.1 `data/products.json`

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
  },
  {
    "sku": "SN-005",
    "name": "Street Sneaker Classic",
    "category": "shoes",
    "price": 99.99,
    "brand": "UrbanKick",
    "in_stock": true,
    "locations": ["Mumbai", "Delhi"]
  },
  {
    "sku": "BT-006",
    "name": "Bluetooth Speaker Mini",
    "category": "electronics",
    "price": 59.99,
    "brand": "SoundWave",
    "in_stock": true,
    "locations": ["Bengaluru", "Chennai"]
  }
]
```

### 1.2 `data/orders.json`

```json
[
  {
    "order_id": "CC-4821",
    "customer_email": "user@example.com",
    "status": "Shipped",
    "items": ["RS-001"],
    "total": 129.99,
    "tracking_number": "TRK-99821",
    "estimated_delivery": "2 days",
    "can_cancel": false
  },
  {
    "order_id": "CC-9910",
    "customer_email": "john@example.com",
    "status": "Processing",
    "items": ["WL-003", "YG-004"],
    "total": 139.98,
    "tracking_number": null,
    "estimated_delivery": "5 days",
    "can_cancel": true
  },
  {
    "order_id": "CC-5001",
    "customer_email": "sara@example.com",
    "status": "Delivered",
    "items": ["TB-002"],
    "total": 144.99,
    "tracking_number": "TRK-55512",
    "estimated_delivery": "Delivered",
    "can_cancel": false
  },
  {
    "order_id": "CC-1234",
    "customer_email": "mike@example.com",
    "status": "Processing",
    "items": ["SN-005", "BT-006"],
    "total": 159.98,
    "tracking_number": null,
    "estimated_delivery": "3 days",
    "can_cancel": true
  }
]
```

### 1.3 `data/coupons.json`

```json
[
  { "code": "SUMMER20", "discount_percent": 20, "active": true },
  { "code": "SAVE10",   "discount_percent": 10, "active": true },
  { "code": "FLAT15",   "discount_percent": 15, "active": true },
  { "code": "EXPIRED5", "discount_percent": 5,  "active": false }
]
```

### 1.4 `data/store_hours.json`

```json
{
  "Bengaluru": {
    "weekday": "9:00 AM – 9:00 PM",
    "weekend": "10:00 AM – 8:00 PM"
  },
  "Mumbai-Central": {
    "weekday": "10:00 AM – 9:00 PM",
    "weekend": "10:00 AM – 7:00 PM"
  },
  "Delhi": {
    "weekday": "9:00 AM – 8:00 PM",
    "weekend": "10:00 AM – 6:00 PM"
  },
  "Chennai": {
    "weekday": "9:30 AM – 8:30 PM",
    "weekend": "10:00 AM – 7:30 PM"
  }
}
```

### 1.5 Verify JSON files

```bash
python -c "import json; print(json.load(open('data/products.json')))"
python -c "import json; print(json.load(open('data/orders.json')))"
python -c "import json; print(json.load(open('data/coupons.json')))"
python -c "import json; print(json.load(open('data/store_hours.json')))"
```

✅ **Phase 1 done when:** All 4 files parse without errors.

---

## Phase 2 — Shared Utilities

**File:** `tools/utils.py`

This file holds everything shared across all tool files — the data loader and the LLM initialiser.
Centralising these prevents duplication and import conflicts.

```python
# tools/utils.py
import json
import os
from pathlib import Path
from langchain_ollama import ChatOllama

# Resolve the data directory relative to project root
DATA_DIR = Path(__file__).parent.parent / "data"


def load_data(filename: str):
    """Load a JSON file from the data/ directory."""
    filepath = DATA_DIR / filename
    with open(filepath, "r") as f:
        return json.load(f)


def get_llm():
    """Return a configured ChatOllama instance."""
    return ChatOllama(model="gemma4:e4b", temperature=0)
```

> **Why `Path(__file__).parent.parent`?**
> Tools are inside `tools/`, so going up two levels reaches the project root where `data/` lives.
> This makes `load_data()` work regardless of which directory you run the script from.

### Verify utils

```bash
python -c "from tools.utils import load_data; print(load_data('products.json')[0]['name'])"
# Expected: Running Shoe X
```

✅ **Phase 2 done when:** `load_data` imports and returns data correctly.

---

## Phase 3 — Part A: Tool Definitions

### 3.1 `tools/product_tools.py`

Contains 5 tools: the 4 from Part A plus extra tools needed by Part C.
All tools follow the same pattern: `load_data()` → filter/search → return formatted string.

```python
# tools/product_tools.py
from langchain.tools import tool
from tools.utils import load_data


@tool
def search_products(query: str, category: str, max_price: float) -> str:
    """
    Search for products in the ShopSphere catalog.

    Args:
        query (str): The search keyword or product name (e.g., 'running shoe').
        category (str): Product category to filter by (e.g., 'shoes', 'electronics', 'fitness').
        max_price (float): Maximum acceptable price in USD.

    Returns:
        str: A formatted list of matching in-stock products with name, price, and SKU.
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
        return f"No in-stock products found for '{query}' in '{category}' under ${max_price}."
    lines = [f"{i+1}. {p['name']} by {p['brand']} — ${p['price']} (SKU: {p['sku']})"
             for i, p in enumerate(results)]
    return f"Found {len(results)} product(s):\n" + "\n".join(lines)


@tool
def get_product_details(sku: str) -> str:
    """
    Get detailed information about a specific product by its SKU.

    Args:
        sku (str): The product SKU identifier (e.g., 'RS-001').

    Returns:
        str: Full product details including name, brand, category, price, stock, and locations.
    """
    products = load_data("products.json")
    product = next((p for p in products if p["sku"] == sku), None)
    if not product:
        return f"No product found with SKU '{sku}'."
    stock_status = "In Stock" if product["in_stock"] else "Out of Stock"
    locations = ", ".join(product["locations"]) if product["locations"] else "Unavailable"
    return (
        f"Product: {product['name']}\n"
        f"Brand: {product['brand']}\n"
        f"Category: {product['category']}\n"
        f"Price: ${product['price']}\n"
        f"Status: {stock_status}\n"
        f"Available at: {locations}"
    )


@tool
def check_inventory(sku: str, location: str) -> str:
    """
    Check whether a product is available at a specific store location.

    Args:
        sku (str): The product SKU to check (e.g., 'RS-001').
        location (str): The store location to check availability at (e.g., 'Bengaluru').

    Returns:
        str: Availability status of the product at the requested location.
    """
    products = load_data("products.json")
    product = next((p for p in products if p["sku"] == sku), None)
    if not product:
        return f"No product found with SKU '{sku}'."
    if not product["in_stock"]:
        return f"'{product['name']}' is currently out of stock everywhere."
    if location in product["locations"]:
        return f"'{product['name']}' is available at {location}."
    return f"'{product['name']}' is NOT available at {location}. Available at: {', '.join(product['locations'])}."


@tool
def get_recommendations(user_id: str) -> str:
    """
    Get product recommendations for a user based on popular in-stock items.

    Args:
        user_id (str): The customer user ID (e.g., 'U-101'). Used for personalisation context.

    Returns:
        str: A list of recommended in-stock products.
    """
    # Simplified: return all in-stock products as recommendations
    # In a real system, this would use purchase history or a recommender model
    products = load_data("products.json")
    in_stock = [p for p in products if p["in_stock"]]
    lines = [f"- {p['name']} by {p['brand']} — ${p['price']}" for p in in_stock]
    return f"Recommended products for you:\n" + "\n".join(lines)


@tool
def apply_coupon(code: str, cart_total: float) -> str:
    """
    Apply a discount coupon code to a shopping cart total.

    Args:
        code (str): The coupon code to apply (e.g., 'SUMMER20').
        cart_total (float): The current cart total in USD before the discount.

    Returns:
        str: The updated cart total after the discount is applied, or an error message.
    """
    coupons = load_data("coupons.json")
    coupon = next((c for c in coupons if c["code"] == code and c["active"]), None)
    if not coupon:
        return f"Coupon '{code}' is invalid or expired."
    discount_amount = cart_total * (coupon["discount_percent"] / 100)
    new_total = cart_total - discount_amount
    return (
        f"Coupon '{code}' applied successfully!\n"
        f"Discount: {coupon['discount_percent']}% = -${discount_amount:.2f}\n"
        f"New Total: ${new_total:.2f}"
    )
```

### 3.2 `tools/order_tools.py`

```python
# tools/order_tools.py
from langchain.tools import tool
from tools.utils import load_data


@tool
def get_order_status(order_id: str, customer_email: str) -> str:
    """
    Retrieve the current status of a customer's order.

    Args:
        order_id (str): The unique order identifier (e.g., 'CC-4821').
        customer_email (str): The email address associated with the order.

    Returns:
        str: Order status details including shipping state, tracking number, and delivery estimate.
    """
    orders = load_data("orders.json")
    order = next(
        (o for o in orders
         if o["order_id"] == order_id and o["customer_email"] == customer_email),
        None
    )
    if not order:
        return f"No order found for ID '{order_id}' with email '{customer_email}'."
    tracking = order["tracking_number"] or "Not yet assigned"
    return (
        f"Order {order['order_id']}:\n"
        f"Status: {order['status']}\n"
        f"Items: {', '.join(order['items'])}\n"
        f"Total: ${order['total']}\n"
        f"Tracking: {tracking}\n"
        f"Estimated Delivery: {order['estimated_delivery']}"
    )


@tool
def cancel_order(order_id: str, reason: str) -> str:
    """
    Cancel an existing order if it is still in a cancellable state.

    Args:
        order_id (str): The unique order identifier to cancel (e.g., 'CC-9910').
        reason (str): The reason for cancellation provided by the customer.

    Returns:
        str: Confirmation of cancellation or an explanation of why it cannot be cancelled.
    """
    orders = load_data("orders.json")
    order = next((o for o in orders if o["order_id"] == order_id), None)
    if not order:
        return f"No order found with ID '{order_id}'."
    if not order.get("can_cancel", False):
        return (
            f"Order '{order_id}' cannot be cancelled — "
            f"it is currently '{order['status']}' and past the cancellation window."
        )
    return (
        f"Order '{order_id}' has been successfully cancelled.\n"
        f"Reason recorded: {reason}\n"
        f"A refund of ${order['total']} will be processed in 3–5 business days."
    )


@tool
def track_shipment(tracking_number: str) -> str:
    """
    Track the current location and status of a shipment using its tracking number.

    Args:
        tracking_number (str): The shipment tracking number (e.g., 'TRK-99821').

    Returns:
        str: Current shipment location and delivery status.
    """
    # Simulated tracking data — keyed by tracking number
    tracking_db = {
        "TRK-99821": {
            "status": "In Transit",
            "location": "Mumbai Hub",
            "eta": "Tomorrow by 8 PM"
        },
        "TRK-55512": {
            "status": "Delivered",
            "location": "Customer Address",
            "eta": "Delivered on May 15"
        },
    }
    info = tracking_db.get(tracking_number)
    if not info:
        return f"No shipment found for tracking number '{tracking_number}'."
    return (
        f"Tracking {tracking_number}:\n"
        f"Status: {info['status']}\n"
        f"Current Location: {info['location']}\n"
        f"ETA: {info['eta']}"
    )


@tool
def process_return(order_id: str, items: str) -> str:
    """
    Initiate a return request for one or more items from a delivered order.

    Args:
        order_id (str): The order ID containing the items to return (e.g., 'CC-5001').
        items (str): Comma-separated SKU codes of items to return (e.g., 'TB-002').

    Returns:
        str: Return request confirmation with instructions, or an error if the order is not eligible.
    """
    orders = load_data("orders.json")
    order = next((o for o in orders if o["order_id"] == order_id), None)
    if not order:
        return f"No order found with ID '{order_id}'."
    if order["status"] != "Delivered":
        return f"Order '{order_id}' is not eligible for return — current status: '{order['status']}'."
    item_list = [s.strip() for s in items.split(",")]
    return (
        f"Return request initiated for Order '{order_id}'.\n"
        f"Items to return: {', '.join(item_list)}\n"
        f"Instructions: Drop off at any ShopSphere store within 7 days.\n"
        f"Refund will be processed within 5–7 business days after receipt."
    )
```

### 3.3 Verify tools load correctly

```bash
python -c "
from tools.product_tools import search_products, get_product_details, check_inventory, get_recommendations, apply_coupon
from tools.order_tools import get_order_status, cancel_order, track_shipment, process_return
print('All tools imported OK')
print('Product tools:', [t.name for t in [search_products, get_product_details, check_inventory, get_recommendations, apply_coupon]])
print('Order tools:', [t.name for t in [get_order_status, cancel_order, track_shipment, process_return]])
"
```

### 3.4 Verify tool logic directly (no LLM needed)

```bash
python -c "
from tools.product_tools import search_products, apply_coupon
from tools.order_tools import get_order_status

# Test search
print(search_products.invoke({'query': 'shoe', 'category': 'shoes', 'max_price': 150.0}))

# Test coupon
print(apply_coupon.invoke({'code': 'SUMMER20', 'cart_total': 200.0}))

# Test order
print(get_order_status.invoke({'order_id': 'CC-4821', 'customer_email': 'user@example.com'}))
"
```

✅ **Phase 3 done when:** All tools import and return correct data from JSON files.

---

## Phase 4 — Part A: Basic Agent

**File:** `part_a_basic_agent.py`

This file must:
- Import 4 tools from Phase 3 (`search_products`, `get_order_status`, `apply_coupon`, `get_store_hours`)
- Define `create_agent(tools, llm)` factory function
- Expose a module-level `agent` variable so `app.py` can import it
- Include a `__main__` block that runs 3 test queries and prints metadata

```python
# part_a_basic_agent.py
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from tools.utils import get_llm
from tools.product_tools import search_products, apply_coupon
from tools.order_tools import get_order_status
from tools.product_tools import get_product_details  # for store hours, use a simple inline tool

# Note: get_store_hours is a product-domain tool — defined here for Part A
from langchain.tools import tool
from tools.utils import load_data

@tool
def get_store_hours(location: str) -> str:
    """
    Get the operating hours for a ShopSphere store at a given location.

    Args:
        location (str): City or store name (e.g., 'Bengaluru', 'Delhi').

    Returns:
        str: Weekday and weekend operating hours for the requested location.
    """
    hours = load_data("store_hours.json")
    info = hours.get(location)
    if not info:
        available = ", ".join(hours.keys())
        return f"No store found for '{location}'. Available locations: {available}"
    return (
        f"ShopSphere {location}:\n"
        f"Mon–Fri: {info['weekday']}\n"
        f"Sat–Sun: {info['weekend']}"
    )


REACT_PROMPT = PromptTemplate.from_template("""You are ShopBot, a helpful retail assistant for ShopSphere.
Use the available tools to answer customer queries accurately.
Always reason step-by-step before calling a tool.
If a tool returns no results, say so clearly — do not guess.

You have access to the following tools:
{tools}

Use EXACTLY this format for every response:

Question: the input question you must answer
Thought: your reasoning about what to do next
Action: the tool name (must be one of [{tool_names}])
Action Input: the input to the tool as a plain string or JSON object
Observation: the result returned by the tool
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now have enough information to answer
Final Answer: your clear, helpful response to the customer

Begin!

Question: {input}
{agent_scratchpad}""")


def create_agent(tools, llm):
    """Build and return a configured ReAct AgentExecutor."""
    agent = create_react_agent(llm=llm, tools=tools, prompt=REACT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=5,
        handle_parsing_errors=True,
        verbose=True
    )


# Module-level agent — imported by app.py
_llm = get_llm()
_tools = [search_products, get_order_status, apply_coupon, get_store_hours]
agent = create_agent(_tools, _llm)


if __name__ == "__main__":
    # A.2 — Print tool metadata
    print("\n" + "="*60)
    print("TOOL METADATA INSPECTION")
    print("="*60)
    for t in _tools:
        print(f"\nTool Name   : {t.name}")
        print(f"Description : {t.description}")
        schema = t.args_schema.schema()
        print("Args Schema :")
        for field, props in schema.get("properties", {}).items():
            ftype = props.get("type", "unknown")
            desc  = props.get("description", "—")
            print(f"  - {field} ({ftype}): {desc}")

    # A.4 — Run 3 test queries
    test_queries = [
        "Find me running shoes under $150 in the shoes category.",
        "What is the status of order #CC-4821 for user@example.com?",
        "Apply coupon SUMMER20 to my $200 cart.",
    ]

    print("\n" + "="*60)
    print("AGENT TEST QUERIES")
    print("="*60)
    for q in test_queries:
        print(f"\nQuery: {q}")
        print("-" * 40)
        result = agent.invoke({"input": q})
        print(f"Final Answer: {result['output']}")
```

### Run Part A

```bash
python part_a_basic_agent.py
```

**Expected:** Tool metadata prints, then 3 agent traces each ending with a Final Answer.

✅ **Phase 4 done when:** Agent completes all 3 queries without errors and uses the correct tool each time.

---

## Phase 5 — Part B: Deep Agent with Tavily

**File:** `part_b_deep_agent.py`

This file must:
- Import the same 4 tools from Phase 3
- Add Tavily as a 5th tool, loaded from `.env`
- Expose a module-level `deep_agent` variable for `app.py`
- Run 3 test queries in `__main__` covering local-only, web-only, and compound scenarios

```python
# part_b_deep_agent.py
import os
from dotenv import load_dotenv
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from tools.utils import get_llm
from tools.product_tools import search_products, apply_coupon
from tools.order_tools import get_order_status
from part_a_basic_agent import get_store_hours  # reuse from Part A

load_dotenv()  # loads TAVILY_API_KEY

# Tavily web search tool — configured for retail context
tavily_tool = TavilySearchResults(
    max_results=3,
    include_domains=[
        "runnersworld.com",
        "sneakersnstuff.com",
        "shopstyle.com",
        "reddit.com",
        "techradar.com"
    ],
    exclude_domains=["spam.com"]
)
tavily_tool.name        = "web_search"
tavily_tool.description = (
    "Search the internet for real-time information about trending products, "
    "brand comparisons, product reviews, or anything not available in local tools. "
    "Use this ONLY when the question requires current or external information. "
    "Do NOT use this for order status, coupons, or store hours."
)

REACT_PROMPT = PromptTemplate.from_template("""You are ShopBot, a smart retail assistant for ShopSphere.
You have access to both local store tools and a live web search tool.
Prefer local tools when the query is about orders, coupons, inventory, or store info.
Use web_search only when the query needs live internet data (trends, reviews, new releases).

Tools available:
{tools}

Use EXACTLY this format:

Question: the input question
Thought: your reasoning — decide which tool is most appropriate
Action: tool name (one of [{tool_names}])
Action Input: input to the tool
Observation: tool result
... (repeat as needed)
Thought: I now have a complete answer
Final Answer: your response to the customer

Begin!

Question: {input}
{agent_scratchpad}""")


def create_deep_agent(tools, llm):
    agent = create_react_agent(llm=llm, tools=tools, prompt=REACT_PROMPT)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=7,   # higher limit — web search adds steps
        handle_parsing_errors=True,
        verbose=True
    )


_llm   = get_llm()
_tools = [search_products, get_order_status, apply_coupon, get_store_hours, tavily_tool]
deep_agent = create_deep_agent(_tools, _llm)


if __name__ == "__main__":
    test_queries = [
        # B.2 — Local only (should NOT use web_search)
        "What is the status of order #CC-4821 for user@example.com?",
        # B.3 — Web only (should use web_search)
        "What are the top trending sneaker brands right now?",
        # B.4 — Compound (web_search → search_products → apply_coupon)
        "Find me trending running shoes under $150 and apply coupon SUMMER20 to a $200 cart.",
    ]

    for q in test_queries:
        print(f"\n{'='*60}\nQuery: {q}\n{'='*60}")
        result = deep_agent.invoke({"input": q})
        print(f"Final Answer: {result['output']}")
```

### Run Part B

```bash
python part_b_deep_agent.py
```

**Expected:**
- Query 1 → uses `get_order_status`, NOT `web_search`
- Query 2 → uses `web_search`, returns live brand names
- Query 3 → chains `web_search` → `search_products` → `apply_coupon`

✅ **Phase 5 done when:** All 3 queries produce correct tool routing as described above.

---

## Phase 6 — Part C: Multi-Agent Orchestration

**File:** `part_c_multi_agent.py`

This file must:
- Import all 9 tools from Phase 3
- Define `make_agent()` factory with domain-scoped system prompt
- Instantiate `product_agent` (5 tools) and `order_agent` (4 tools)
- Define `keyword_router(query)` → returns `'product'` or `'order'`
- Define `orchestrate(query)` → routes and dispatches, logs which agent was used
- Run 5 test queries in `__main__`

```python
# part_c_multi_agent.py
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from tools.utils import get_llm
from tools.product_tools import (
    search_products,
    get_product_details,
    check_inventory,
    get_recommendations,
    apply_coupon,
)
from tools.order_tools import (
    get_order_status,
    cancel_order,
    track_shipment,
    process_return,
)

_llm = get_llm()

REACT_TEMPLATE = """You are a ShopSphere assistant specialising in {domain}.
Only use the tools available to you. Do not attempt to answer questions outside your domain.
If the query is outside your domain, say: "This is outside my area — please contact the right team."

Tools:
{tools}

Tool names: [{tool_names}]

Use this format:

Question: {input}
Thought: your step-by-step reasoning
Action: tool name
Action Input: tool input
Observation: tool result
... (repeat as needed)
Thought: I now have the final answer
Final Answer: your response

{agent_scratchpad}"""


def make_agent(tools: list, domain: str) -> AgentExecutor:
    """Create a domain-specialised AgentExecutor."""
    prompt = PromptTemplate.from_template(REACT_TEMPLATE.replace("{domain}", domain))
    agent  = create_react_agent(llm=_llm, tools=tools, prompt=prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=5,
        handle_parsing_errors=True,
        verbose=True
    )


# Specialised agents
product_agent = make_agent(
    tools=[search_products, get_product_details, check_inventory, get_recommendations, apply_coupon],
    domain="products, inventory, recommendations, and promotions"
)

order_agent = make_agent(
    tools=[get_order_status, cancel_order, track_shipment, process_return],
    domain="order management, cancellations, shipment tracking, and returns"
)


# Keyword lists for routing
ORDER_KEYWORDS = [
    "order", "status", "cancel", "return", "refund",
    "shipment", "tracking", "delivered", "dispatch", "track"
]


def keyword_router(query: str) -> str:
    """
    Route a query to 'product' or 'order' based on keyword matching.
    Defaults to 'product' for ambiguous queries.
    """
    query_lower = query.lower()
    if any(kw in query_lower for kw in ORDER_KEYWORDS):
        return "order"
    return "product"


def orchestrate(query: str) -> str:
    """Route query to the appropriate specialised agent and return its response."""
    route = keyword_router(query)
    print(f"\n[Router] '{query[:50]}...' → routed to: {route.upper()} AGENT")

    if route == "order":
        result = order_agent.invoke({"input": query})
    else:
        result = product_agent.invoke({"input": query})

    return result["output"]


if __name__ == "__main__":
    test_queries = [
        "Show me running shoes under $130.",                             # → product
        "What is the status of order #CC-9910 for john@example.com?",  # → order
        "I want to return items from order #CC-5001.",                  # → order
        "Check if SKU TB-002 is available in Bengaluru.",              # → product
        "I need something comfortable for yoga.",                       # → product (ambiguous)
    ]

    print("\n" + "="*60)
    print("MULTI-AGENT ROUTING TEST")
    print("="*60)

    for q in test_queries:
        print(f"\nQuery: {q}")
        answer = orchestrate(q)
        print(f"Answer: {answer}")
```

### Run Part C

```bash
python part_c_multi_agent.py
```

**Expected routing:**

| Query | Route | Agent |
|-------|-------|-------|
| "running shoes under $130" | `product` | Product Agent |
| "status of order #CC-9910" | `order` | Order Agent |
| "return items from order" | `order` | Order Agent |
| "SKU TB-002 in Bengaluru" | `product` | Product Agent |
| "something comfortable for yoga" | `product` | Product Agent |

✅ **Phase 6 done when:** All 5 queries route correctly and agents return meaningful responses.

---

## Phase 7 — Streamlit UI

**File:** `app.py`

Build this **last** — it only imports from the already-working agent files.

```python
# app.py
import streamlit as st

st.set_page_config(
    page_title="ShopSphere Assistant",
    page_icon="🛍️",
    layout="centered"
)

# ── Sidebar ──────────────────────────────────────────────────
st.sidebar.title("🛍️ ShopSphere")
st.sidebar.markdown("Intelligent Retail Assistant")
st.sidebar.divider()

mode = st.sidebar.radio(
    "Agent Mode",
    options=["Part A — Basic Agent", "Part B — Deep Agent (Web)", "Part C — Multi-Agent"],
    index=2  # default to Part C
)

st.sidebar.divider()
st.sidebar.caption("LLM: gemma4:e4b via Ollama")
st.sidebar.caption("Web Search: Tavily API")

# ── Load agents (cached so they don't reload on every interaction) ──
@st.cache_resource
def load_basic_agent():
    from part_a_basic_agent import agent
    return agent

@st.cache_resource
def load_deep_agent():
    from part_b_deep_agent import deep_agent
    return deep_agent

@st.cache_resource
def load_orchestrator():
    from part_c_multi_agent import orchestrate, keyword_router
    return orchestrate, keyword_router

# ── Main UI ───────────────────────────────────────────────────
st.title("🛍️ ShopSphere Assistant")
st.caption(f"Running in: **{mode}**")

# Initialise chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display existing messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("route"):
            st.caption(f"🔀 Routed to: {msg['route']}")

# User input
if user_input := st.chat_input("Ask ShopBot anything..."):
    # Store and display user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("ShopBot is thinking..."):
            route_label = None
            try:
                if mode == "Part A — Basic Agent":
                    agent = load_basic_agent()
                    result = agent.invoke({"input": user_input})
                    response = result["output"]

                elif mode == "Part B — Deep Agent (Web)":
                    agent = load_deep_agent()
                    result = agent.invoke({"input": user_input})
                    response = result["output"]

                else:  # Part C
                    orchestrate, keyword_router = load_orchestrator()
                    route_label = keyword_router(user_input).upper() + " AGENT"
                    response = orchestrate(user_input)

            except Exception as e:
                response = f"⚠️ Error: {str(e)}\n\nMake sure Ollama is running (`ollama serve`)."

        st.write(response)
        if route_label:
            st.caption(f"🔀 Routed to: {route_label}")

    # Store assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "route": route_label
    })

# Clear chat button
if st.session_state.messages:
    if st.sidebar.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
```

### Run the Streamlit app

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

**Test these queries in the UI:**

| Mode | Sample Query |
|------|-------------|
| Part A | "Find me electronics under $100" |
| Part B | "What sneaker brands are trending right now?" |
| Part C | "Cancel my order #CC-9910" |
| Part C | "Show me fitness products" |

✅ **Phase 7 done when:** UI loads, chat works in all 3 modes, Part C shows routing label.

---

## Verification Checklist

Run through this end-to-end before submitting:

```
[ ] Phase 0 — ollama serve running, gemma4:e4b responds
[ ] Phase 1 — all 4 JSON files parse cleanly
[ ] Phase 2 — load_data('products.json') returns list from tools/utils.py
[ ] Phase 3 — all 9 tools import, direct .invoke() calls return correct data
[ ] Phase 4 — part_a_basic_agent.py runs, prints metadata, 3 queries pass
[ ] Phase 5 — part_b_deep_agent.py runs, Q1 uses local tool, Q2 uses Tavily, Q3 chains
[ ] Phase 6 — part_c_multi_agent.py runs, 5 queries route correctly
[ ] Phase 7 — streamlit run app.py opens, all 3 modes work in chat UI
```

---

## Known Gotchas & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| `Connection refused` on LLM calls | Ollama not running | Run `ollama serve` in a separate terminal |
| `Model not found` error | Model not pulled | Run `ollama pull gemma4:e4b` |
| `ModuleNotFoundError: tools` | Running script from wrong directory | Always `cd shopsphere` first, then run scripts |
| `FileNotFoundError: data/products.json` | Wrong working directory | Use `Path(__file__).parent.parent / "data"` in `utils.py` (already done) |
| Agent stuck in loop / hits max_iterations | LLM not following ReAct format | Increase `max_iterations`, set `handle_parsing_errors=True` (already set) |
| Tavily returns no results | API key missing or wrong | Check `.env` has correct `TAVILY_API_KEY`, run `python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TAVILY_API_KEY'))"` |
| Part C import fails in `app.py` | Agent module-level code runs on import | Use `@st.cache_resource` to lazy-load agents (already done in `app.py`) |
| Streamlit reruns on every message | Normal Streamlit behaviour | Use `st.session_state` to persist chat history (already done) |
| `get_store_hours` not found in Part B | It's defined in `part_a_basic_agent.py` | Import it: `from part_a_basic_agent import get_store_hours` |

---

## File-by-File Spec Summary

| File | Exports | Imports From | Phase |
|------|---------|-------------|-------|
| `data/*.json` | — | — | 1 |
| `tools/utils.py` | `load_data`, `get_llm` | — | 2 |
| `tools/product_tools.py` | 5 `@tool` functions | `tools.utils` | 3 |
| `tools/order_tools.py` | 4 `@tool` functions | `tools.utils` | 3 |
| `part_a_basic_agent.py` | `agent`, `create_agent`, `get_store_hours` | `tools.*`, `tools.utils` | 4 |
| `part_b_deep_agent.py` | `deep_agent`, `create_deep_agent` | `tools.*`, `part_a_basic_agent` | 5 |
| `part_c_multi_agent.py` | `product_agent`, `order_agent`, `orchestrate`, `keyword_router` | `tools.*`, `tools.utils` | 6 |
| `app.py` | — (entry point) | `part_a_basic_agent`, `part_b_deep_agent`, `part_c_multi_agent` | 7 |

---

*ShopSphere Implementation Plan — companion to ShopSphere_PRD.md*
*Build order: Phase 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7. Never skip ahead.*
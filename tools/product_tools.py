from langchain.tools import tool

from tools.utils import load_data


@tool
def search_products(query: str, category: str, max_price: float) -> str:
    """
    Search for in-stock products by keyword, category, and budget.

    Args:
        query: Search keyword to match against product name or brand.
        category: Product category: shoes, mobiles, or laptops.
        max_price: Maximum allowed product price.

    Returns:
        A formatted list of matching products, or a no-results message.
    """
    products = load_data("products.json")
    query_lower = query.lower().strip()
    category_lower = category.lower().strip()
    # Split into individual tokens so "running shoes" matches "Running Shoe" (singular),
    # and a brand search for "nike air" still works word-by-word.
    query_tokens = query_lower.split()

    def _matches_query(product: dict) -> bool:
        name = product["name"].lower()
        brand = product["brand"].lower()
        return any(token in name or token in brand for token in query_tokens)

    results = [
        product
        for product in products
        if _matches_query(product)
        and product["category"].lower() == category_lower
        and product["price"] <= max_price
        and product["in_stock"]
    ]

    if not results:
        return (
            f"No in-stock products found for '{query}' in '{category}' under "
            f"${max_price:.2f}."
        )

    lines = [
        f"{index + 1}. {product['name']} by {product['brand']} - "
        f"${product['price']:.2f} (SKU: {product['sku']})"
        for index, product in enumerate(results)
    ]
    return f"Found {len(results)} product(s):\n" + "\n".join(lines)


@tool
def get_product_details(sku: str) -> str:
    """
    Return complete details for a single product SKU.

    Args:
        sku: Stock-keeping unit identifier, for example NK-001.

    Returns:
        A formatted detail view for the product, or an error if not found.
    """
    products = load_data("products.json")
    product = next((item for item in products if item["sku"] == sku), None)
    if product is None:
        return f"No product found with SKU '{sku}'."

    stock_label = "In Stock" if product["in_stock"] else "Out of Stock"
    locations = ", ".join(product["locations"]) if product["locations"] else "Unavailable"
    return (
        f"Product: {product['name']}\n"
        f"SKU: {product['sku']}\n"
        f"Brand: {product['brand']}\n"
        f"Category: {product['category']}\n"
        f"Price: ${product['price']:.2f}\n"
        f"Status: {stock_label}\n"
        f"Available at: {locations}"
    )


@tool
def check_inventory(sku: str, location: str) -> str:
    """
    Check whether a product is available in a specific store location.

    Args:
        sku: Product SKU to inspect.
        location: City or store location to check.

    Returns:
        A human-readable availability response for the requested location.
    """
    products = load_data("products.json")
    product = next((item for item in products if item["sku"] == sku), None)
    if product is None:
        return f"No product found with SKU '{sku}'."

    if not product["in_stock"]:
        return f"'{product['name']}' is currently out of stock at all locations."

    if location in product["locations"]:
        return f"'{product['name']}' is available at {location}."

    available = ", ".join(product["locations"]) if product["locations"] else "none"
    return f"'{product['name']}' is not available at {location}. Available at: {available}."


@tool
def get_recommendations(user_id: str) -> str:
    """
    Recommend products from currently in-stock catalog items.

    Args:
        user_id: Customer identifier used as recommendation context.

    Returns:
        A formatted recommendation list of in-stock products.
    """
    products = load_data("products.json")
    in_stock_products = [product for product in products if product["in_stock"]]
    if not in_stock_products:
        return f"No recommendations are currently available for user '{user_id}'."

    lines = [
        f"- {product['name']} by {product['brand']} - ${product['price']:.2f} "
        f"(SKU: {product['sku']})"
        for product in in_stock_products
    ]
    return f"Recommended products for user '{user_id}':\n" + "\n".join(lines)


@tool
def apply_coupon(code: str, cart_total: float) -> str:
    """
    Apply an active coupon code to a cart total.

    Args:
        code: Coupon code string such as SUMMER20.
        cart_total: Cart amount before discount.

    Returns:
        Discount details and updated total, or an invalid-coupon message.
    """
    coupons = load_data("coupons.json")
    normalized_code = code.upper().strip()
    coupon = next(
        (item for item in coupons if item["code"].upper() == normalized_code and item["active"]),
        None,
    )
    if coupon is None:
        return f"Coupon '{code}' is invalid or expired."

    discount_amount = cart_total * (coupon["discount_percent"] / 100)
    new_total = cart_total - discount_amount
    return (
        f"Coupon '{coupon['code']}' applied successfully!\n"
        f"Discount: {coupon['discount_percent']}% = -${discount_amount:.2f}\n"
        f"New Total: ${new_total:.2f}"
    )

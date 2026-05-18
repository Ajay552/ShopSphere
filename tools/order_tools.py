from langchain.tools import tool

from tools.utils import load_data


@tool
def get_order_status(order_id: str, customer_email: str) -> str:
    """
    Retrieve the current status and delivery details for a customer order.

    Args:
        order_id: Unique order identifier such as CC-4821.
        customer_email: Email address associated with the order.

    Returns:
        A formatted order status response, or an error when no match is found.
    """
    orders = load_data("orders.json")
    order = next(
        (
            item
            for item in orders
            if item["order_id"] == order_id and item["customer_email"] == customer_email
        ),
        None,
    )
    if order is None:
        return f"No order found for ID '{order_id}' with email '{customer_email}'."

    tracking_label = order["tracking_number"] or "Not yet assigned"
    return (
        f"Order {order['order_id']}:\n"
        f"Status: {order['status']}\n"
        f"Items: {', '.join(order['items'])}\n"
        f"Total: ${order['total']:.2f}\n"
        f"Tracking: {tracking_label}\n"
        f"Estimated Delivery: {order['estimated_delivery']}"
    )


@tool
def cancel_order(order_id: str, reason: str) -> str:
    """
    Cancel an order if it is still within the cancellation window.

    Args:
        order_id: The order ID to cancel.
        reason: Customer-provided cancellation reason.

    Returns:
        Cancellation confirmation with refund details, or an eligibility message.
    """
    orders = load_data("orders.json")
    order = next((item for item in orders if item["order_id"] == order_id), None)
    if order is None:
        return f"No order found with ID '{order_id}'."

    if not order.get("can_cancel", False):
        return (
            f"Order '{order_id}' cannot be cancelled because it is currently "
            f"'{order['status']}' and outside the cancellation window."
        )

    return (
        f"Order '{order_id}' has been successfully cancelled.\n"
        f"Reason recorded: {reason}\n"
        f"A refund of ${order['total']:.2f} will be processed in 3-5 business days."
    )


@tool
def track_shipment(tracking_number: str) -> str:
    """
    Track shipment progress for a given tracking number.

    Args:
        tracking_number: Shipment tracking identifier such as TRK-99821.

    Returns:
        Shipment status details resolved from order data, or a not-found message.
    """
    orders = load_data("orders.json")
    order = next(
        (
            item
            for item in orders
            if item.get("tracking_number") and item["tracking_number"] == tracking_number
        ),
        None,
    )
    if order is None:
        return f"No shipment found for tracking number '{tracking_number}'."

    if order["status"] == "Delivered":
        location = "Customer Address"
        eta = "Delivered"
    elif order["status"] == "Shipped":
        location = "In Transit Hub"
        eta = order["estimated_delivery"]
    else:
        location = "Warehouse"
        eta = order["estimated_delivery"]

    return (
        f"Tracking {tracking_number}:\n"
        f"Status: {order['status']}\n"
        f"Current Location: {location}\n"
        f"ETA: {eta}"
    )


@tool
def process_return(order_id: str, items: str) -> str:
    """
    Create a return request for items from a delivered order.

    Args:
        order_id: Order identifier that contains items to be returned.
        items: Comma-separated SKU values requested for return.

    Returns:
        Return request confirmation with next steps, or an eligibility error.
    """
    orders = load_data("orders.json")
    order = next((item for item in orders if item["order_id"] == order_id), None)
    if order is None:
        return f"No order found with ID '{order_id}'."

    if order["status"] != "Delivered":
        return (
            f"Order '{order_id}' is not eligible for return - current status: "
            f"'{order['status']}'."
        )

    requested_items = [sku.strip() for sku in items.split(",") if sku.strip()]
    if not requested_items:
        return "Please provide at least one item SKU to process the return."

    return (
        f"Return request initiated for Order '{order_id}'.\n"
        f"Items to return: {', '.join(requested_items)}\n"
        "Instructions: Drop off at any ShopSphere store within 7 days.\n"
        "Refund will be processed within 5-7 business days after item receipt."
    )

"""Read-only data access returning JSON-compatible dicts for agent tools."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from tools.db import ensure_db_seeded, get_session
from tools.models import Coupon, Order, Product, StoreHours


def _product_to_dict(product: Product) -> dict:
    return {
        "sku": product.sku,
        "name": product.name,
        "category": product.category,
        "price": product.price,
        "brand": product.brand,
        "in_stock": product.in_stock,
        "locations": [loc.location for loc in product.locations],
    }


def _order_to_dict(order: Order) -> dict:
    return {
        "order_id": order.order_id,
        "customer_email": order.customer_email,
        "status": order.status,
        "items": [item.sku for item in order.items],
        "total": order.total,
        "tracking_number": order.tracking_number,
        "estimated_delivery": order.estimated_delivery,
        "can_cancel": order.can_cancel,
    }


def get_products() -> list[dict]:
    """Return all products with locations aggregated like products.json."""
    ensure_db_seeded()
    with get_session() as session:
        products = session.scalars(
            select(Product).options(selectinload(Product.locations))
        ).all()
        return [_product_to_dict(product) for product in products]


def get_product_by_sku(sku: str) -> dict | None:
    """Return a single product dict by SKU, or None if not found."""
    ensure_db_seeded()
    with get_session() as session:
        product = session.scalar(
            select(Product)
            .where(Product.sku == sku)
            .options(selectinload(Product.locations))
        )
        return _product_to_dict(product) if product else None


def get_orders() -> list[dict]:
    """Return all orders with line items aggregated like orders.json."""
    ensure_db_seeded()
    with get_session() as session:
        orders = session.scalars(select(Order).options(selectinload(Order.items))).all()
        return [_order_to_dict(order) for order in orders]


def get_order_by_id(order_id: str) -> dict | None:
    """Return a single order dict by order_id, or None if not found."""
    ensure_db_seeded()
    with get_session() as session:
        order = session.scalar(
            select(Order)
            .where(Order.order_id == order_id)
            .options(selectinload(Order.items))
        )
        return _order_to_dict(order) if order else None


def get_coupons() -> list[dict]:
    """Return all coupons as a list of dicts like coupons.json."""
    ensure_db_seeded()
    with get_session() as session:
        coupons = session.scalars(select(Coupon)).all()
        return [
            {
                "code": coupon.code,
                "discount_percent": coupon.discount_percent,
                "active": coupon.active,
            }
            for coupon in coupons
        ]


def get_store_hours() -> dict[str, dict]:
    """Return store hours keyed by location like store_hours.json."""
    ensure_db_seeded()
    with get_session() as session:
        rows = session.scalars(select(StoreHours)).all()
        return {
            row.location: {"weekday": row.weekday, "weekend": row.weekend}
            for row in rows
        }

"""Seed ShopSphere SQLite database from JSON files in data/."""

from __future__ import annotations

import json

from sqlalchemy import delete, func, select

from tools.db import DATA_DIR, get_engine, get_session, init_db
from tools.models import (
    Base,
    Coupon,
    Order,
    OrderItem,
    Product,
    ProductLocation,
    StoreHours,
)


def _load_json(filename: str):
    filepath = DATA_DIR / filename
    with open(filepath, "r", encoding="utf-8") as file:
        return json.load(file)


def seed_from_json(force: bool = False) -> None:
    """
    Import products, orders, coupons, and store hours from data/*.json.

    Args:
        force: When True, drop and recreate all tables before seeding.
    """
    engine = get_engine()

    if force:
        Base.metadata.drop_all(engine)

    init_db()

    with get_session() as session:
        product_count = session.scalar(select(func.count()).select_from(Product))
        if product_count and product_count > 0 and not force:
            return

        if force or (product_count and product_count > 0):
            session.execute(delete(ProductLocation))
            session.execute(delete(Product))
            session.execute(delete(OrderItem))
            session.execute(delete(Order))
            session.execute(delete(Coupon))
            session.execute(delete(StoreHours))
            session.commit()

        products = _load_json("products.json")
        orders = _load_json("orders.json")
        coupons = _load_json("coupons.json")
        store_hours = _load_json("store_hours.json")

        for row in products:
            session.add(
                Product(
                    sku=row["sku"],
                    name=row["name"],
                    category=row["category"],
                    price=float(row["price"]),
                    brand=row["brand"],
                    in_stock=bool(row["in_stock"]),
                )
            )
            for location in row.get("locations", []):
                session.add(ProductLocation(sku=row["sku"], location=location))

        for row in orders:
            session.add(
                Order(
                    order_id=row["order_id"],
                    customer_email=row["customer_email"],
                    status=row["status"],
                    total=float(row["total"]),
                    tracking_number=row.get("tracking_number"),
                    estimated_delivery=row["estimated_delivery"],
                    can_cancel=bool(row.get("can_cancel", False)),
                )
            )
            for sku in row.get("items", []):
                session.add(OrderItem(order_id=row["order_id"], sku=sku))

        for row in coupons:
            session.add(
                Coupon(
                    code=row["code"],
                    discount_percent=int(row["discount_percent"]),
                    active=bool(row["active"]),
                )
            )

        for location, hours in store_hours.items():
            session.add(
                StoreHours(
                    location=location,
                    weekday=hours["weekday"],
                    weekend=hours["weekend"],
                )
            )

        session.commit()

"""SQLAlchemy ORM models for ShopSphere SQLite storage."""

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    in_stock: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    locations: Mapped[list["ProductLocation"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )


class ProductLocation(Base):
    __tablename__ = "product_locations"

    sku: Mapped[str] = mapped_column(String, ForeignKey("products.sku"), primary_key=True)
    location: Mapped[str] = mapped_column(String, primary_key=True)

    product: Mapped["Product"] = relationship(back_populates="locations")


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String, primary_key=True)
    customer_email: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    tracking_number: Mapped[str | None] = mapped_column(String, nullable=True)
    estimated_delivery: Mapped[str] = mapped_column(Text, nullable=False)
    can_cancel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(String, ForeignKey("orders.order_id"), primary_key=True)
    sku: Mapped[str] = mapped_column(String, primary_key=True)

    order: Mapped["Order"] = relationship(back_populates="items")


class Coupon(Base):
    __tablename__ = "coupons"

    code: Mapped[str] = mapped_column(String, primary_key=True)
    discount_percent: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class StoreHours(Base):
    __tablename__ = "store_hours"

    location: Mapped[str] = mapped_column(String, primary_key=True)
    weekday: Mapped[str] = mapped_column(Text, nullable=False)
    weekend: Mapped[str] = mapped_column(Text, nullable=False)

from enum import Enum
from sqlalchemy import Boolean, Column, Enum as SQLEnum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    foods = relationship("Food", back_populates="category")


class Food(Base):
    __tablename__ = "foods"
    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    image = Column(String(500), nullable=True)
    is_available = Column(Boolean, nullable=False, default=True)
    restaurant = relationship("Restaurant", back_populates="foods")
    category = relationship("Category", back_populates="foods")
    reviews = relationship("Review", back_populates="food", cascade="all, delete-orphan")


class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=True)
    user = relationship("User")
    restaurant = relationship("Restaurant")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    cart = relationship("Cart", back_populates="items")
    food = relationship("Food")
    __table_args__ = (UniqueConstraint("cart_id", "food_id", name="uq_cart_food"),)


class OrderStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    READY = "ready"
    ASSIGNED = "assigned"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryStatus(str, Enum):
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    PICKED_UP = "picked_up"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    delivery_person_id = Column(Integer, ForeignKey("delivery_persons.id"), nullable=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    delivery_status = Column(SQLEnum(DeliveryStatus), nullable=True)
    total_price = Column(Numeric(10, 2), nullable=False)
    delivery_address = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    user = relationship("User")
    restaurant = relationship("Restaurant")
    delivery_person = relationship("DeliveryPerson")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(150), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False)
    order = relationship("Order", back_populates="items")
    food = relationship("Food")


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=True)
    food_id = Column(Integer, ForeignKey("foods.id", ondelete="CASCADE"), nullable=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    user = relationship("User")
    restaurant = relationship("Restaurant", back_populates="reviews")
    food = relationship("Food", back_populates="reviews")
    __table_args__ = (UniqueConstraint("user_id", "restaurant_id", name="uq_user_restaurant_review"), UniqueConstraint("user_id", "food_id", name="uq_user_food_review"))
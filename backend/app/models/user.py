from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"
    RESTAURANT = "restaurant"
    DELIVERY_PERSON = "delivery_person"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    restaurant = relationship("Restaurant", foreign_keys=[restaurant_id])


class DeliveryPerson(Base):
    __tablename__ = "delivery_persons"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    phone = Column(String(20), nullable=False)
    vehicle_type = Column(String(50), nullable=False)
    vehicle_number = Column(String(50), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User")